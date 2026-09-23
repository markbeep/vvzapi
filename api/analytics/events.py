"""Classification, query analysis and event recording for vvzapi analytics.

Single place that decides:
* how traffic is classified (browser / crawler / app / unknown),
* how a search query is decomposed (filters, operators, boolean shape),
* what a request or search event looks like before it reaches ClickHouse.

Keeping the definitions here means Prometheus, ClickHouse and the Grafana
dashboards cannot drift apart.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from timeit import default_timer
from typing import Final, Literal

from fastapi import Request

from api.env import Settings
from api.analytics.clickhouse import writer
from api.util.parse_query import AND, OR, Operator
from api.analytics.privacy import hasher
from api.analytics.prometheus import SEARCH_STAGE_DURATION

# `crawler` = search engines, AI crawlers, SEO/monitoring/scanner bots.
# `app`     = a programmatic client: HTTP library, SDK, CLI or custom client.
ClientType = Literal["browser", "crawler", "app", "unknown"]
RequestKind = Literal["web", "api", "asset", "monitoring"]
QueryType = Literal["empty", "free_text", "keyword", "fielded", "boolean"]
BooleanOp = Literal["single", "and", "or", "mixed", "none"]

# A filter leaf as it is stored: (key, operator, negated).
FilterTerm = tuple[str, str, int]


@dataclass(frozen=True)
class _Rule:
    family: str
    client_type: ClientType
    pattern: re.Pattern[str]


def _rules(client_type: ClientType, families: dict[str, str]) -> tuple[_Rule, ...]:
    return tuple(
        _Rule(family, client_type, re.compile(pattern, re.IGNORECASE))
        for family, pattern in families.items()
    )


# Deliberately coarse families: they become Prometheus label values, so the
# cardinality has to stay bounded regardless of how many UAs show up.
_CRAWLER_RULES: Final[tuple[_Rule, ...]] = _rules(
    "crawler",
    {
        "googlebot": r"googlebot|google-inspectiontool|googleother|feedfetcher|google-read-aloud",
        "bingbot": r"bingbot|bingpreview|adidxbot",
        "applebot": r"applebot",
        "ai-crawler": r"gptbot|oai-searchbot|chatgpt-user|claudebot|claude-web|anthropic|ccbot|perplexitybot|amazonbot|bytespider|meta-externalagent|diffbot",
        "seo-crawler": r"ahrefs|semrush|mj12bot|dotbot|rogerbot|screaming ?frog|blexbot|serpstat|dataforseo|petalbot|yandex|baiduspider|duckduckbot|sogou",
        "social-preview": r"facebookexternalhit|twitterbot|linkedinbot|telegrambot|discordbot|whatsapp|slackbot|embedly|pinterest|vkshare|redditbot",
        "uptime-monitor": r"uptimerobot|pingdom|statuscake|betteruptime|updown|hetrixtools|site24x7|newrelic|datadog",
        "security-scanner": r"censys|zgrab|masscan|\bnmap|internetmeasurement|shodan|expanse|paloalto|netsystemsresearch|nuclei|nikto|sqlmap",
    },
)

_APP_RULES: Final[tuple[_Rule, ...]] = _rules(
    "app",
    {
        "python-requests": r"python-requests|requests/\d",
        "httpx": r"python-httpx|httpx/",
        "aiohttp": r"aiohttp",
        "python-urllib": r"python-urllib|urllib\d?/",
        "scrapy": r"scrapy",
        "curl": r"\bcurl/",
        "wget": r"\bwget",
        "go-http-client": r"go-http-client|golang",
        "okhttp": r"okhttp",
        "node-fetch": r"node-fetch|undici|axios/|got/|superagent|request/\d",
        "java": r"\bjava/|apache-httpclient|jersey|httpclient",
        "dotnet": r"dotnet|restsharp|windows-?powershell|azure|\.net",
        "php": r"\bphp/|guzzle|symfony",
        "ruby": r"\bruby|faraday|httparty|rest-client",
        "rust": r"\breqwest|ureq|rust",
        "dart": r"\bdart/|http-client-dart",
        "deno": r"\bdeno/",
        "bun": r"\bbun/",
        "postman": r"postmanruntime|postman",
        "insomnia": r"insomnia",
        "httpie": r"httpie",
        "k6": r"\bk6/|k6-",
        "locust": r"locust",
        "haskell": r"\bhaskell|http-conduit",
        "elixir": r"hackney|mint/|\belixir",
    },
)

# Generic automation that did not name a known crawler. Kept last so that a
# specific app (e.g. `python-requests`) wins over the bare `bot` heuristic.
_GENERIC_CRAWLER: Final[tuple[_Rule, ...]] = (
    _Rule(
        "other-crawler",
        "crawler",
        re.compile(r"bot\b|spider|crawler|slurp", re.IGNORECASE),
    ),
)

_RULES: Final[tuple[_Rule, ...]] = _CRAWLER_RULES + _APP_RULES + _GENERIC_CRAWLER

_BROWSER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"mozilla/.*(chrome|firefox|safari|edg|opr|gecko|trident)", re.IGNORECASE
)

_ASSET_PATTERN: Final[re.Pattern[str]] = re.compile(r"\.\w+$")

_API_PREFIXES: Final[tuple[str, ...]] = ("/search", "/v0", "/v1", "/v2", "/api")

_API_ENDPOINT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^/api/(v\d+)/([a-z]+)")

# Query keys that only narrow a text search (as opposed to picking attributes).
_CONTENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "title",
        "title_german",
        "title_english",
        "descriptions",
        "descriptions_german",
        "descriptions_english",
    }
)

_BOOLEAN_PATTERN: Final[re.Pattern[str]] = re.compile(r"(^|\s)(or|and)(\s|$)")

# A "fielded" term looks like `y:2026`, `c=2`, `credits>=5`, ...
_OPERATOR_PATTERN: Final[re.Pattern[str]] = re.compile(r"[a-z_]+\s*(!=|>=|<=|=|>|<|:)")

# Query parameters that get their own column in the `requests` table. Everything
# else lands in a single bounded `other_params` string, so no client can grow
# the table schema.
_NAMED_PARAMS: Final[frozenset[str]] = frozenset(
    {"q", "page", "limit", "offset", "order_by", "order", "view"}
)


def _match_rule(user_agent: str | None) -> _Rule | None:
    if not user_agent:
        return None
    for rule in _RULES:
        if rule.pattern.search(user_agent):
            return rule
    return None


def client_family(user_agent: str | None) -> str:
    """Bounded client family used as a label, e.g. `python-requests`, `okhttp`."""
    rule = _match_rule(user_agent)
    if rule is not None:
        return rule.family
    if not user_agent:
        return "none"
    return "other"


def classify_client(user_agent: str | None, has_sec_fetch: bool) -> ClientType:
    """Classify a client as `browser`, `crawler`, `app` or `unknown`.

    `has_sec_fetch` should reflect whether any `Sec-Fetch-*` header is present,
    which real browsers always send. Known crawler/app signatures win over that
    heuristic, so a Chromium-based crawler is still a crawler.
    """
    rule = _match_rule(user_agent)
    if rule is not None:
        return rule.client_type
    if has_sec_fetch:
        return "browser"
    if not user_agent:
        return "unknown"
    if _BROWSER_PATTERN.search(user_agent):
        return "browser"
    # Neither a known crawler nor browser-shaped: some programmatic client.
    return "app"


def classify_request_kind(path: str) -> RequestKind:
    """Coarsely label a request path, e.g. for separating UI from API traffic."""
    if path.startswith("/metrics"):
        return "monitoring"
    if path.startswith("/static") or _ASSET_PATTERN.search(path):
        return "asset"
    if path.startswith(_API_PREFIXES):
        return "api"
    return "web"


def api_endpoint(path: str) -> str:
    """Normalise an API path to a bounded endpoint label, e.g. `v2/search`."""
    match = _API_ENDPOINT_PATTERN.match(path)
    if match is not None:
        return f"{match.group(1)}/{match.group(2)}"
    return "other"


def classify_client_for_request(request: Request | None) -> ClientType:
    if request is None:
        return "unknown"
    return classify_client(
        request.headers.get("user-agent"), "sec-fetch-mode" in request.headers
    )


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("cf-connecting-ip") or request.headers.get(
        "x-forwarded-for"
    )
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def categorize_query(raw_query: str, filter_keys: set[str]) -> QueryType:
    """Bucket a raw query string into a small, stable set of shapes.

    Note that a bare word such as `dynamics` is turned into an implicit `title`
    filter by the parser, so the shape is decided on the raw query string; the
    parsed `filter_keys` only separate explicit content filters from attribute
    filters.
    """
    stripped = raw_query.strip()
    if not stripped:
        return "empty"
    lowered = stripped.lower()
    if _BOOLEAN_PATTERN.search(lowered):
        return "boolean"
    if not _OPERATOR_PATTERN.search(lowered):
        return "free_text"
    if filter_keys <= _CONTENT_KEYS:
        return "keyword"
    return "fielded"


def query_filters(op: AND | OR) -> list[FilterTerm]:
    """Leaf filters of a parsed query as (key, operator, negated) triples.

    `LogicalOperator.__iter__` flattens nested AND/OR groups, so this returns
    the terms in the order the user wrote them.
    """
    return [
        (str(filter_.key), filter_.operator.value, int(filter_.operator is Operator.ne))
        for filter_ in op
    ]


def boolean_shape(op: AND | OR, term_count: int) -> BooleanOp:
    """How boolean logic was used: single term, plain AND, plain OR or mixed."""
    if term_count == 0:
        return "none"
    if term_count == 1:
        return "single"
    has_and = False
    has_or = False
    stack: list[AND | OR] = [op]
    while stack:
        node = stack.pop()
        if isinstance(node, OR):
            has_or = True
        else:
            has_and = True
        stack.extend(child for child in node.ops if isinstance(child, (AND, OR)))
    if has_and and has_or:
        return "mixed"
    return "or" if has_or else "and"


_stage_collector: ContextVar[dict[str, float] | None] = ContextVar(
    "vvzapi_search_stages", default=None
)


@contextmanager
def collect_stages() -> Iterator[dict[str, float]]:
    """Collect per-stage timings for the current search into a dict.

    Stages run concurrently (`asyncio.gather`), so each task mutates the same
    dict object rather than rebinding the ContextVar.
    """
    stages: dict[str, float] = {}
    token = _stage_collector.set(stages)
    try:
        yield stages
    finally:
        _stage_collector.reset(token)


@contextmanager
def observe_stage(stage: str) -> Iterator[None]:
    """Time a search stage, feeding both the histogram and the current search."""
    start = default_timer()
    try:
        yield
    finally:
        elapsed = default_timer() - start
        SEARCH_STAGE_DURATION.labels(stage=stage).observe(elapsed)
        collector = _stage_collector.get()
        if collector is not None:
            collector[stage] = collector.get(stage, 0.0) + elapsed


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _int_param(params: Mapping[str, str], key: str) -> int:
    value = params.get(key, "")
    return int(value) if value.isdigit() else 0


def record_request(request: Request, status_code: int) -> None:
    """Record one request row. Cheap and non-blocking; never raises."""
    if not Settings().clickhouse.url:
        return
    user_agent = request.headers.get("user-agent", "")
    params = dict(request.query_params)
    other = {
        key: value[:100] for key, value in params.items() if key not in _NAMED_PARAMS
    }
    writer.enqueue(
        "requests",
        {
            "timestamp": _timestamp(),
            "path": request.url.path,
            "method": request.method,
            "hostname": request.url.hostname or "",
            "status": status_code,
            "request_kind": classify_request_kind(request.url.path),
            "client_type": classify_client(
                user_agent or None, "sec-fetch-mode" in request.headers
            ),
            "client_family": client_family(user_agent or None),
            "user_agent": user_agent[:100],
            "ip_hash": hasher.hash_ip(client_ip(request))[:16],
            "referrer": (request.headers.get("referer") or "")[:500],
            "url": str(request.url)[:1000],
            "query_text": params.get("q", "")[:500],
            "page": _int_param(params, "page"),
            "result_limit": _int_param(params, "limit"),
            "page_offset": _int_param(params, "offset"),
            "order_by": params.get("order_by", "")[:50],
            "view": params.get("view", "")[:20],
            "other_params": ",".join(
                f"{key}={value}" for key, value in sorted(other.items())
            )[:300],
        },
    )


def record_search(
    request: Request | None,
    *,
    source: str,
    raw_query: str,
    parsed_query: str,
    filters: list[FilterTerm],
    boolean_op: str,
    query_type: str,
    result_count: int,
    exec_time_ms: float,
    duration_ms: float,
    stages_ms: Mapping[str, float],
    page: int,
    limit: int,
    order_by: str,
    order: str,
    view: str,
) -> None:
    """Record one search row, including how the query was built."""
    if not Settings().clickhouse.url:
        return
    if request is None:
        client_type: str = "unknown"
        family = "none"
        ip = "unknown"
    else:
        client_type = classify_client(
            request.headers.get("user-agent"), "sec-fetch-mode" in request.headers
        )
        family = client_family(request.headers.get("user-agent"))
        ip = client_ip(request)
    writer.enqueue(
        "searches",
        {
            "timestamp": _timestamp(),
            "source": source,
            "client_type": client_type,
            "client_family": family,
            "query_type": query_type,
            "boolean_op": boolean_op,
            "order_by": order_by,
            "sort_dir": order,
            "view": view,
            "page": page,
            "result_limit": limit,
            "term_count": len(filters),
            "filter_count": len({key for key, _, _ in filters}),
            "result_count": result_count,
            "zero_results": int(result_count == 0),
            "exec_time_ms": round(exec_time_ms, 3),
            "duration_ms": round(duration_ms, 3),
            "parse_ms": round(stages_ms.get("parse", 0.0) * 1000, 3),
            "count_ms": round(stages_ms.get("count", 0.0) * 1000, 3),
            "fetch_ms": round(stages_ms.get("fetch", 0.0) * 1000, 3),
            "ratings_ms": round(stages_ms.get("ratings", 0.0) * 1000, 3),
            "ip_hash": hasher.hash_ip(ip)[:16],
            "query_text": raw_query[:500],
            "parsed_query": parsed_query[:500],
            # ClickHouse reads named tuples as JSON objects
            # (input_format_json_named_tuples_as_objects).
            "filters": [
                {"key": key, "operator": operator, "negated": negated}
                for key, operator, negated in filters
            ],
        },
    )

"""Per-scrape-run analytics.

Scrapy keeps one ``StatsCollector`` per spider; the counters used here are
maintained by the default middlewares and extensions (requests, status codes,
``httpcache/*``, ``log_count/*``, ``retry/*``) or incremented by
``DatabasePipeline`` (item counts). A logging handler additionally buffers every
WARNING+ record, including the message text.

Both buffers are written in synchronous inserts from ``scraper.main`` *after*
the reactor has stopped, so no blocking network call runs while spiders crawl.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast, override
from uuid import uuid4

from scrapy import Spider, signals
from scrapy.crawler import Crawler

from api.analytics.clickhouse import insert_rows_sync

logger = logging.getLogger(__name__)

RUNS_TABLE = "scrape_runs"
LOGS_TABLE = "scrape_logs"
RUN_ID = uuid4().hex  # one id per scraper process, shared by all its spiders

# Bounds so a pathological run cannot grow the log table without limit: at most
# 1000 rows of at most 1000 chars, i.e. <= 1 MiB per run. The errors/warnings
# counters in scrape_runs stay exact regardless.
MAX_LOGS = 1000
MAX_MESSAGE_CHARS = 1000

_pending: list[dict[str, object]] = []
_logs: list[dict[str, object]] = []


def _int(stats: Mapping[str, object], key: str) -> int:
    value = stats.get(key, 0)
    return int(value) if isinstance(value, (int, float)) else 0


def _status_class(stats: Mapping[str, object], base: int) -> int:
    return sum(
        _int(stats, f"downloader/response_status_count/{code}")
        for code in range(base, base + 100)
    )


def _timestamp(value: object) -> str:
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, (int, float)):
        moment = datetime.fromtimestamp(value, UTC)
    else:
        moment = datetime.now(UTC)
    return moment.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def build_row(
    spider_name: str, stats: Mapping[str, object], reason: str
) -> dict[str, object]:
    elapsed_time = stats.get("elapsed_time_seconds") or 0.0
    if not isinstance(elapsed_time, (int, float)):
        elapsed_time = 0.0
    return {
        "timestamp": _timestamp(stats.get("finish_time")),
        "run_id": RUN_ID,
        "spider": spider_name,
        "started_at": _timestamp(stats.get("start_time")),
        "duration_seconds": round(float(elapsed_time), 3),
        "finish_reason": reason,
        "requests": _int(stats, "downloader/request_count"),
        "responses": _int(stats, "downloader/response_count"),
        "status_2xx": _status_class(stats, 200),
        "status_3xx": _status_class(stats, 300),
        "status_4xx": _status_class(stats, 400),
        "status_5xx": _status_class(stats, 500),
        "exceptions": _int(stats, "downloader/exception_count"),
        "retries": _int(stats, "retry/count"),
        "items_scraped": _int(stats, "item_scraped_count"),
        "items_new": _int(stats, "vvzapi/items_new"),
        "items_updated": _int(stats, "vvzapi/items_updated"),
        "units_new": _int(stats, "vvzapi/units_new"),
        "units_updated": _int(stats, "vvzapi/units_updated"),
        "lecturers_new": _int(stats, "vvzapi/lecturers_new"),
        "lecturers_updated": _int(stats, "vvzapi/lecturers_updated"),
        "errors": _int(stats, "log_count/ERROR"),
        "warnings": _int(stats, "log_count/WARNING"),
        "cache_hits": _int(stats, "httpcache/hit"),
        "cache_misses": _int(stats, "httpcache/miss"),
        "cache_stores": _int(stats, "httpcache/store"),
    }


class _ScrapeLogHandler(logging.Handler):
    """Buffer WARNING+ records with their message text."""

    @override
    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.levelno < logging.WARNING or len(_logs) >= MAX_LOGS:
                return
            # `scrapy.utils.log.SpiderLoggerAdapter` injects this as
            # `extra["spider"]`; records from scrapy's own loggers have none.
            # LogRecord does not declare it, so `getattr` is untyped - pin it to
            # `object` and narrow with isinstance instead of trusting it.
            spider = cast(object, getattr(record, "spider", None))
            _logs.append(
                {
                    "timestamp": _timestamp(record.created),
                    "run_id": RUN_ID,
                    "spider": spider.name if isinstance(spider, Spider) else "",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage()[:MAX_MESSAGE_CHARS],
                }
            )
        except Exception:  # noqa: BLE001 - a log handler must never raise
            pass


_handler: _ScrapeLogHandler | None = None


class ScrapeRunAnalytics:
    """Scrapy extension: buffer the per-spider stats row at close and install
    the log handler once per process."""

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "ScrapeRunAnalytics":
        global _handler
        if _handler is None:
            _handler = _ScrapeLogHandler(level=logging.WARNING)
            logging.getLogger().addHandler(_handler)
        extension = cls()
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        return extension

    def spider_closed(self, spider: Spider, reason: str) -> None:
        stats = spider.crawler.stats
        _pending.append(
            build_row(spider.name, stats.get_stats() if stats else {}, reason)
        )


def record_scrape_run() -> None:
    """Write the buffered rows to ClickHouse. Never raises."""
    batches = [(RUNS_TABLE, _pending), (LOGS_TABLE, _logs)]
    for table, buffer in batches:
        rows = list(buffer)
        buffer.clear()
        if not rows:
            continue
        try:
            insert_rows_sync(table, rows)
        except Exception as error:  # noqa: BLE001 - analytics must not break the run
            logger.warning("failed to record %s analytics: %s", table, error)

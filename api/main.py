from __future__ import annotations

import re
from typing import cast, final

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.analytics.events import (
    api_endpoint,
    classify_client,
    classify_request_kind,
    client_family,
    record_request,
)
from api.analytics.prometheus import (
    API_CLIENT_REQUESTS,
    CLIENT_TYPE_REQUESTS,
)
from api.core.env import Settings
from api.core.version import get_api_version
from api.mcp import mcp_lifespan, mount_mcp
from api.routers.v0_router import router as v0_router
from api.routers.v1_router import router as v1_router
from api.web.routes import router as web_router

# Configure OpenTelemetry tracing
settings = Settings()
if settings.jaeger_endpoint:
    resource = Resource.create({"service.name": settings.otel_service_name})
    tracer_provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint=settings.jaeger_endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

app = FastAPI(
    title="VVZ API",
    version=get_api_version(),
    description=(
        "v0 endpoints are experimental and can break at any point. "
        "Use the versioned endpoints (v1) for ensured backwards compatibility."
        "\n\n## MCP Server\n\n"
        "The same data is also exposed as a "
        "[Model Context Protocol](https://modelcontextprotocol.io) server at `/mcp` "
        "(streamable HTTP, served by this API process). Point MCP clients "
        "(Claude Code/Desktop, Cursor, VS Code, ...) at `https://vvzapi.ch/mcp` to call the "
        "typed tools (`search_units`, `get_unit`, `list_units`, ...) instead of hand-rolling "
        "HTTP requests.\n\n"
        "```json\n"
        '{\n  "mcpServers": {\n    "vvz": { "type": "http", "url": "https://vvzapi.ch/mcp" }\n  }\n}\n'
        "```"
    ),
    lifespan=mcp_lifespan,
)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/static/*")
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

app.include_router(v0_router)
app.include_router(v1_router)
# Serve the MCP server at /mcp; registered before the /{root} catch-all below.
mount_mcp(app)
app.include_router(web_router)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# enables rate limitting if needed (like for data dump endpoint)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # pyright: ignore[reportArgumentType]


async def send_plausible_event(request: Request):
    plausible_url = Settings().plausible_url
    if not plausible_url:
        return
    headers = {
        "Content-Type": "application/json",
    }
    if user_agent := request.headers.get("user-agent"):
        headers["User-Agent"] = user_agent

    if request.headers.get("cf-connecting-ip"):
        headers["X-Forwarded-For"] = request.headers["cf-connecting-ip"]
    elif request.headers.get("x-forwarded-for"):
        headers["X-Forwarded-For"] = request.headers["x-forwarded-for"]
    elif request.client:
        headers["X-Forwarded-For"] = request.client.host

    body = {
        "name": "pageview",
        "url": str(request.url),
        "domain": request.url.hostname,
    }
    if request.headers.get("referer"):
        body["referrer"] = request.headers.get("referer")

    try:
        async with httpx.AsyncClient() as client:
            await client.post(plausible_url, json=body, headers=headers, timeout=10)
    except httpx.ConnectTimeout:
        print("Plausible connection timed out")


def _record_client_metrics(request: Request, path: str) -> None:
    user_agent = request.headers.get("user-agent")
    client_type = classify_client(user_agent, "sec-fetch-mode" in request.headers)
    request_kind = classify_request_kind(path)
    CLIENT_TYPE_REQUESTS.labels(
        client_type=client_type,
        request_kind=request_kind,
    ).inc()
    if request_kind == "api":
        API_CLIENT_REQUESTS.labels(
            endpoint=api_endpoint(path),
            client_type=client_type,
            client_family=client_family(user_agent),
        ).inc()


@final
class AnalyticsMiddleware:
    """Record per-request metrics, a ClickHouse row, cache headers and a pageview.

    Pure ASGI on purpose. `BaseHTTPMiddleware` runs the wrapped app in its own
    task and waits for that task to emit its first message, so an app that
    returns without responding makes it raise
    `RuntimeError("No response returned.")`. Any client that disconnects before
    the first byte can trigger that, and the long-lived `/mcp` SSE endpoint hits
    it routinely because its handler cancels its own task group on
    `http.disconnect`. Handling the messages directly has no such race.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        has_extension = re.search(r"\.\w+$", path) is not None
        # /metrics is scraped continuously; counting it would drown out real traffic.
        tracked = not path.startswith("/metrics")
        status_code = 0

        async def send_and_record(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = cast(int, message["status"])
                if 200 <= status_code < 300:
                    headers = MutableHeaders(scope=message)
                    if "cache-control" not in headers:
                        headers["Cache-Control"] = (
                            f"public, max-age={settings.cache_expiry}"
                        )
                if tracked:
                    _record_client_metrics(request, path)
                    # Assets and /metrics are skipped; everything else is
                    # recorded, including 404s, because the status code is part
                    # of the row.
                    if not has_extension:
                        record_request(request, status_code)
            await send(message)

        await self.app(scope, receive, send_and_record)

        # Runs once the response is complete, where the background task used to.
        # A request that never produced a response is not a pageview.
        if (
            tracked
            and not has_extension
            and status_code not in (0, 404, 307)
            and settings.plausible_url
        ):
            await send_plausible_event(request)


app.add_middleware(AnalyticsMiddleware)

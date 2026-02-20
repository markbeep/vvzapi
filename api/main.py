from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Annotated, Awaitable, Callable, Literal

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.background import BackgroundTask

from api.env import Settings
from api.models import (
    Course,
    LearningUnit,
    Lecturer,
    Rating,
    Section,
    UnitExaminerLink,
    UnitLecturerLink,
)
from api.routers.v1.units import get_unit
from api.routers.v1_router import router as v1_router
from api.routers.v2.search import search_units
from api.routers.v2_router import router as v2_router
from api.util.db import aget_session
from api.util.parse_query import QueryKey
from api.util.sections import get_parent_from_unit
from api.util.sitemap import generate_sitemap
from api.util.templates import catalog_response
from api.util.version import get_api_version

# Configure OpenTelemetry tracing
settings = Settings()
if settings.jaeger_endpoint:
    resource = Resource.create({"service.name": settings.otel_service_name})
    tracer_provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint=settings.jaeger_endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

app = FastAPI(title="VVZ API", version=get_api_version())
FastAPIInstrumentor.instrument_app(app, excluded_urls="/static/*")

app.include_router(v1_router)
app.include_router(v2_router)
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


def send_analytics_event(request: Request):
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
        "props": dict(request.query_params),
    }
    if request.headers.get("referer"):
        body["referrer"] = request.headers.get("referer")

    httpx.post(
        plausible_url,
        json=body,
        headers=headers,
        timeout=10,
    )


@app.middleware("http")
async def analytics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[StreamingResponse]]
):
    response: StreamingResponse = await call_next(request)

    if 200 <= response.status_code < 300:
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = (
                f"Cache-Control: public, max-age={Settings().cache_expiry}"
            )

    has_extension = re.search(r"\.\w+$", request.url.path) is not None
    if (
        response.status_code != 404
        and response.status_code != 307
        and Settings().plausible_url
        and not has_extension
    ):
        task = BackgroundTask(send_analytics_event, request)
        response.background = task

    return response


@app.get("/", include_in_schema=False)
async def root(
    query: Annotated[str | None, Query(alias="q"), str] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    order_by: QueryKey = "title_english",
    order: str = "asc",
    view: Literal["big", "compact"] = "big",
):
    with tracer.start_as_current_span("root_search") as span:
        span.set_attribute("query", query or "")
        span.set_attribute("page", page)
        span.set_attribute("limit", limit or "default")
        span.set_attribute("order_by", order_by)
        span.set_attribute("order", order)
        span.set_attribute("view", view)

        if not query:
            return catalog_response("Index.Empty")

        if limit is None:
            limit = 20 if view == "big" else 50

        results = await search_units(
            query,
            offset=(page - 1) * limit,
            limit=limit,
            order_by=order_by,
            order=order,
        )

        span.set_attribute("result_count", results.total)

        if results.total == 1:
            values = list(results.results.values())
            if len(values) == 1:
                first = values[0].latest_unit()
                if first:
                    return RedirectResponse(f"/unit/{first.id}", status_code=303)

        return catalog_response(
            "Index.Results",
            query=query,
            page=page,
            limit=limit,
            order_by=order_by,
            order=order,
            results=results,
            view=view,
        )


class RecursiveSection(BaseModel):
    section: Section
    sub_sections: list[RecursiveSection] = []


@app.get("/unit/{unit_id}", include_in_schema=False)
async def unit_detail(
    request: Request,
    unit_id: int,
    session: Annotated[AsyncSession, Depends(aget_session)],
    query: Annotated[str | None, Query(alias="q"), str] = None,
):
    with tracer.start_as_current_span("unit_detail") as span:
        span.set_attribute("unit_id", unit_id)

        unit = await get_unit(unit_id, session)
        if not unit:  # TODO: redirect to 404 page once implemented
            return HTMLResponse(status_code=404)

        span.set_attribute("unit_number", unit.number or "")
        span.set_attribute("unit_title", unit.title_english or "")

        with tracer.start_as_current_span("lecturer"):
            lecturers = (
                await session.exec(
                    select(Lecturer)
                    .join(
                        UnitLecturerLink,
                        col(UnitLecturerLink.lecturer_id) == Lecturer.id,
                    )
                    .where(UnitLecturerLink.unit_id == unit_id)
                )
            ).all()
            span.set_attribute("lecturer_count", len(lecturers))

        with tracer.start_as_current_span("examiner"):
            examiners = (
                await session.exec(
                    select(Lecturer)
                    .join(
                        UnitExaminerLink,
                        col(UnitExaminerLink.lecturer_id) == Lecturer.id,
                    )
                    .where(UnitExaminerLink.unit_id == unit_id)
                )
            ).all()
            span.set_attribute("examiner_count", len(examiners))

        with tracer.start_as_current_span("courses"):
            courses = (
                await session.exec(select(Course).where(Course.unit_id == unit_id))
            ).all()
            span.set_attribute("course_count", len(courses))

        with tracer.start_as_current_span("sections"):
            sections = (await session.exec(get_parent_from_unit(unit_id))).all()
            span.set_attribute("section_count", len(sections))

        with tracer.start_as_current_span("semkezs"):
            semkezs = (
                await session.exec(
                    select(LearningUnit.id, LearningUnit.semkez)
                    .where(LearningUnit.number == unit.number)
                    .distinct()
                )
            ).all()
            span.set_attribute("semkez_count", len(semkezs))

        with tracer.start_as_current_span("section_tree"):
            # create tree structure of offered in sections
            section_ids = {
                section.id: RecursiveSection(section=section) for section in sections
            }
            root_sections: list[RecursiveSection] = []
            for section in sections:
                if section.parent_id and section.parent_id in section_ids:
                    parent_section = section_ids[section.parent_id]
                    parent_section.sub_sections.append(section_ids[section.id])
                else:
                    root_sections.append(section_ids[section.id])

        # allows us to add canonical links to the newest unit
        newest_unit_id, _ = max(
            [(id, sk.replace("W", "0").replace("S", "1")) for id, sk in semkezs],
            key=lambda x: x[1],
        )

        with tracer.start_as_current_span("rating"):
            rating = None
            average_rating = "n/a"
            if unit.number:
                rating = await session.get(Rating, unit.number)
                average_rating = rating.average() if rating else "n/a"

        links = {
            str(request.url_for("unit_detail", unit_id=newest_unit_id)): "cannonical"
        }

        span.set_attribute("newest_unit_id", newest_unit_id)
        span.set_attribute(
            "average_rating",
            average_rating if isinstance(average_rating, (int, float)) else -1,
        )

        return catalog_response(
            "Unit.Index",
            request=request,
            query=query or "",
            unit=unit,
            sections=root_sections,
            courses=courses,
            lecturers=lecturers,
            examiners=examiners,
            semkezs=semkezs,
            is_outdated=newest_unit_id != unit.id,
            newest_unit_id=newest_unit_id,
            average_rating=average_rating,
            links=links,
        )


@app.get("/guide", include_in_schema=False)
async def guide():
    return catalog_response("Guide")


@app.get("/{root}", include_in_schema=False)
async def root_static(root: str):
    if root not in [
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "apple-touch-icon.png",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico",
        "site.webmanifest",
        "sitemap.xml",
        "robots.txt",
    ]:
        return HTMLResponse(status_code=404)

    if root == "sitemap.xml":
        generate_sitemap(Settings().sitemap_expiry)
        return FileResponse(
            Path(__file__).parent / "static" / "sitemap" / "sitemap.xml",
            media_type="application/xml",
        )
    elif root == "robots.txt":
        robots_path = Path(__file__).parent / "static" / "robots.txt"
        if robots_path.exists():
            return FileResponse(robots_path, media_type="text/plain")
        return HTMLResponse(status_code=404)

    root_path = Path(__file__).parent / "static" / root
    if root_path.exists():
        match root_path.suffix:
            case ".png":
                return FileResponse(root_path, media_type="image/png")
            case ".ico":
                return FileResponse(root_path, media_type="image/x-icon")
            case ".webmanifest":
                return FileResponse(root_path, media_type="application/manifest+json")
            case _:
                return FileResponse(root_path)

    return HTMLResponse(status_code=404)


@app.get("/sitemap/{sitemap_file}", include_in_schema=False)
async def sitemap_files(sitemap_file: str):
    if re.match(r"sitemap(-\w+?)?\.xml", sitemap_file) is None:
        return HTMLResponse(status_code=404)
    sitemap_path = Path(__file__).parent / "static" / "sitemap" / sitemap_file
    if sitemap_path.exists():
        return FileResponse(sitemap_path, media_type="application/xml")
    return HTMLResponse(status_code=404)


@app.get("/static/{file_path:path}", include_in_schema=False)
async def astro_files(file_path: str):
    if file_path.startswith("components"):
        """
        JS / CSS files can be requested in Jinjax templates by using
        the relative path under the templates/ directory (i.e. {#js pages/Index/empty.js #}).
        This will then automatically fetch /static/components/pages/Index/empty.js to add the
        script into the header.
        """
        if not file_path.endswith(".js") and not file_path.endswith(".css"):
            return HTMLResponse(status_code=404)
        static_dir = Path("api/templates")
        file_path = file_path.removeprefix("components/")
    else:
        static_dir = Path("api/static")

    # ----------------------------------
    # | Prevent directory traversal.   |
    # | Ensures the real path is still |
    # | within the static directory.   |
    # ----------------------------------
    static_dir = static_dir.absolute()
    requested_path = static_dir / file_path.lstrip("/")
    shared_path = os.path.commonprefix([static_dir, os.path.realpath(requested_path)])
    if shared_path != str(static_dir):
        print(f"Directory traversal attempt detected: {requested_path = }")
        raise HTTPException(status_code=404, detail="Not found")
    # ----------------------------------

    requested_file = static_dir / requested_path
    if not requested_file.exists() or not requested_file.is_file():
        requested_file /= "index.html"
        if not requested_file.exists() or not requested_file.is_file():
            raise HTTPException(status_code=404, detail="Not Found")

    # Determine media type based on file extension
    extension = requested_file.suffix.lower()
    media_types = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".xml": "application/xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".eot": "application/vnd.ms-fontobject",
        ".otf": "font/otf",
    }
    media_type = media_types.get(extension, "application/octet-stream")
    return StreamingResponse(requested_file.open("rb"), media_type=media_type)

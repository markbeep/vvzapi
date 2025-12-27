from __future__ import annotations

from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, Query, Request
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from sqlmodel import Session, col, select
from starlette.background import BackgroundTask
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from jinja2_pluralize import pluralize_dj  # pyright: ignore[reportUnknownVariableType,reportMissingTypeStubs]
import httpx
from jinja2_htmlmin import minify_loader

from api.env import Settings
from api.models import (
    Course,
    LearningUnit,
    Lecturer,
    Section,
    UnitExaminerLink,
    UnitLecturerLink,
)
from api.routers.v1_router import router as v1_router
from api.routers.v2_router import router as v2_router
from api.routers.v2.search import QueryKey, search_units
from api.routers.v1.units import get_unit
from api.util.db import get_session
from api.util.sections import get_parent_from_unit
from api.util.version import get_api_version


app = FastAPI(title="VVZ API", version=get_api_version())
app.include_router(v1_router)
app.include_router(v2_router)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

templates = Jinja2Templates(
    env=Environment(
        loader=minify_loader(
            FileSystemLoader(str(Path(__file__).parent / "templates")),
            remove_comments=True,
            remove_empty_space=True,
            remove_all_empty_space=True,
            reduce_boolean_attributes=True,
        )
    )
)
templates.env.filters["pluralize"] = pluralize_dj  # pyright: ignore[reportUnknownMemberType]
templates.env.filters["trim_float"] = (  # pyright: ignore[reportUnknownMemberType]
    lambda x: round(cast(float, x), 3) if x % 1 else int(cast(float, x))  # pyright: ignore[reportUnknownLambdaType]
)


def send_analytics_event(request: Request):
    plausible_url = Settings().plausible_url
    if not plausible_url:
        return
    headers = {
        "Content-Type": "application/json",
        "User-Agent": request.headers.get("user-agent", "vvzapi"),
    }
    if request.client:
        headers["X-Forwarded-For"] = request.client.host

    httpx.post(
        plausible_url,
        json={
            "name": "pageview",
            "url": str(request.url),
            "domain": request.url.hostname,
        },
        headers=headers,
        timeout=10,
    )


@app.middleware("http")
async def analytics_middleware(request: Request, call_next: Any):
    response: StreamingResponse = await call_next(request)
    if (
        not Settings().plausible_url
        and not request.url.path.startswith("/api")
        and not request.url.path == "/"
        and not request.url.path.startswith("/docs")
    ):
        return response
    task = BackgroundTask(send_analytics_event, request)
    response.background = task

    if 200 <= response.status_code < 300:
        response.headers["Cache-Control"] = (
            f"Cache-Control: public, max-age={Settings().cache_expiry}"
        )
    return response


@app.get("/", include_in_schema=False)
async def root(
    session: Annotated[Any, Depends(get_session)],
    query: Annotated[str | None, Query(alias="q"), str] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order_by: QueryKey = "title_english",
    order: str = "asc",
):
    if not query:
        return templates.TemplateResponse(
            "root_search.html", {"request": {}, "version": get_api_version()}
        )

    results = await search_units(
        query,
        session,
        offset=(page - 1) * limit,
        limit=limit,
        order_by=order_by,
        order=order,
    )

    if results.total == 1:
        values = list(results.results.values())
        if len(values) == 1:
            first = values[0].latest_unit()
            if first:
                return RedirectResponse(f"/unit/{first.id}", status_code=303)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": {},
            "version": get_api_version(),
            "query": query,
            "page": page,
            "limit": limit,
            "order_by": order_by,
            "order": order,
            "results": results,
        },
    )


class RecursiveSection(BaseModel):
    section: Section
    sub_sections: list[RecursiveSection] = []


@app.get("/unit/{unit_id}", include_in_schema=False)
async def unit_detail(
    request: Request,
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    unit = await get_unit(unit_id, session)
    if not unit:  # TODO: redirect to 404 page once implemented
        return HTMLResponse(status_code=404)

    lecturers = session.exec(
        select(Lecturer)
        .join(UnitLecturerLink, col(UnitLecturerLink.lecturer_id) == Lecturer.id)
        .where(UnitLecturerLink.unit_id == unit_id)
    ).all()
    examiners = session.exec(
        select(Lecturer)
        .join(UnitExaminerLink, col(UnitExaminerLink.lecturer_id) == Lecturer.id)
        .where(UnitExaminerLink.unit_id == unit_id)
    ).all()
    courses = session.exec(select(Course).where(Course.unit_id == unit_id)).all()
    sections = session.exec(get_parent_from_unit(unit_id)).all()
    semkezs = session.exec(
        select(LearningUnit.id, LearningUnit.semkez)
        .where(LearningUnit.number == unit.number)
        .distinct()
    ).all()

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

    return templates.TemplateResponse(
        "unit_detail.html",
        {
            "request": request,
            "version": get_api_version(),
            "unit": unit,
            "sections": root_sections,
            "courses": courses,
            "lecturers": lecturers,
            "examiners": examiners,
            "semkezs": semkezs,
        },
    )


@app.get("/guide", include_in_schema=False)
async def guide():
    return templates.TemplateResponse(
        "guide.html",
        {
            "request": {},
            "version": get_api_version(),
        },
    )


@app.get("/{favicon}", include_in_schema=False)
async def favicon(favicon: str):
    if favicon not in [
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "apple-touch-icon.png",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico",
        "site.webmanifest",
    ]:
        return HTMLResponse(status_code=404)

    favicon_path = Path(__file__).parent / "static" / favicon
    if favicon_path.exists():
        return HTMLResponse(favicon_path.read_bytes(), media_type="image/x-icon")
    return HTMLResponse(status_code=404)


@app.get("/static/{file_path:path}", include_in_schema=False)
async def static_files(file_path: str):
    if file_path not in [
        "globals.css",
        "opensearch.xml",
    ]:
        return HTMLResponse(status_code=404)
    static_path = Path(__file__).parent / "static" / file_path
    if static_path.exists():
        return FileResponse(static_path)
    return HTMLResponse(status_code=404)

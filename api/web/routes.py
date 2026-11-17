from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from opentelemetry import trace
from pydantic import BaseModel
from sqlalchemy import true
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.analytics.events import classify_client
from api.analytics.prometheus import INDEX_VIEWS
from api.catalog.models import (
    Course,
    HTTPCache,
    LatestSemkez,
    LearningUnit,
    Lecturer,
    Rating,
    Section,
    SectionPathView,
    UnitExaminerLink,
    UnitLecturerLink,
)
from api.catalog.sections import get_parent_from_unit
from api.catalog.semkez import semkez_to_comparable
from api.core.db import aget_meta_session, aget_session
from api.core.env import Settings
from api.routers.v1.units import get_unit
from api.search.query import QueryKey, offered_in_query
from api.search.router import run_search
from api.web.search_context import (
    build_new_search_context,
    build_new_search_state,
    compose_query,
)
from api.web.sitemap import generate_sitemap
from api.web.templates import catalog_response
from api.webhook import send_flagged_webhook

router = APIRouter()
tracer = trace.get_tracer(__name__)


@router.get("/", include_in_schema=False)
async def root(
    request: Request,
    query: Annotated[str | None, Query(alias="q"), str] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    order_by: QueryKey = "title_english",
    order: str | None = None,
):
    if order is None:
        order = "desc" if order_by in ("year", "coursereview") else "asc"

    with tracer.start_as_current_span("root_search") as span:
        span.set_attribute("query", query or "")
        span.set_attribute("page", page)
        span.set_attribute("limit", limit or "default")
        span.set_attribute("order_by", order_by)
        span.set_attribute("order", order)

        if not query:
            INDEX_VIEWS.labels(
                client_type=classify_client(
                    request.headers.get("user-agent"),
                    "sec-fetch-mode" in request.headers,
                ),
            ).inc()
            if query == "":
                return RedirectResponse(
                    url="/",
                    status_code=303,
                )
            return catalog_response(
                "Index.Empty",
                headers={"Vary": "FX-Request"},
            )

        if limit is None:
            limit = 20

        # swap out results with fixijs if available, else handle request as normal
        layout_name = "Index.WithLayout"
        if request.headers.get("fx-request") == "true":
            layout_name = "Index.Results"

        try:
            results = await run_search(
                query,
                offset=(page - 1) * limit,
                limit=limit,
                order_by=order_by,
                order=order,
                source="web",
                view="big",  # keep the existing analytics series for the single web layout
                page=page,
                request=request,
            )
        except HTTPException as exc:
            if exc.status_code != 400:
                raise
            return catalog_response(
                layout_name,
                status_code=400,
                query=query,
                page=page,
                limit=limit,
                order_by=order_by,
                order=order,
                results=None,
                error=str(exc.detail),
                headers={"Vary": "FX-Request"},
            )

        span.set_attribute("result_count", results.total)
        span.set_attribute("exec_time_ms", results.exec_time_ms)

        if results.total == 1:
            values = list(results.results.values())
            if len(values) == 1:
                first = values[0].latest_unit()
                if first:
                    return RedirectResponse(
                        f"/unit/{first.id}#q={quote(query, safe="!~*'()")}",
                        status_code=303,
                        headers={"Vary": "FX-Request"},
                    )

        return catalog_response(
            layout_name,
            query=query,
            page=page,
            limit=limit,
            order_by=order_by,
            order=order,
            results=results,
            headers={
                "Vary": "FX-Request",
            },
        )


@router.get("/new", include_in_schema=False)
async def new_search(
    request: Request,
    q: Annotated[str, Query(description="Raw search query.")] = "",
    program: Annotated[
        int,
        Query(ge=0, description="Root programme section id; 0 means any."),
    ] = 0,
    section: Annotated[
        int,
        Query(ge=0, description="Section id below the programme; 0 means any."),
    ] = 0,
    newest: Annotated[
        bool,
        Query(description="Only the newest semester in the catalogue."),
    ] = False,
    semester: Annotated[
        list[str] | None,
        Query(description="Semester type filter: W (Autumn) or S (Spring)."),
    ] = None,
    level: Annotated[
        list[str] | None,
        Query(description="Degree-program level filter, e.g. BSC or MSC."),
    ] = None,
    dept: Annotated[
        list[str] | None,
        Query(description="Department id filter."),
    ] = None,
    min_credits: Annotated[
        int,
        Query(ge=0, le=20, description="Minimum ECTS; 0 means any."),
    ] = 0,
    min_rating: Annotated[
        float,
        Query(ge=0, le=5, description="Minimum CourseReview average; 0 means any."),
    ] = 0,
    sort: Annotated[
        Literal["title", "number", "credits", "latest", "coursereview"],
        Query(description="Sort key."),
    ] = "title",
    order: Annotated[
        Literal["asc", "desc"] | None,
        Query(description="Sort direction; defaults per sort key."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=20, le=100, description="Results per page (20, 40, 60, 80 or 100)."),
    ] = 20,
    page: Annotated[int, Query(ge=1, description="Page number.")] = 1,
):
    state = await build_new_search_state(
        q=q,
        program=program,
        section=section,
        newest=newest,
        semesters=semester or (),
        levels=level or (),
        depts=dept or (),
        min_credits=min_credits,
        min_rating=min_rating,
        sort=sort,
        order=order,
        limit=limit,
        page=page,
    )
    query = compose_query(state)
    results = None
    error = None
    if query:
        try:
            results = await run_search(
                query,
                offset=(state.page - 1) * state.limit,
                limit=state.limit,
                order_by=state.order_by,
                order=state.order,
                source="web",
                view="new",
                page=state.page,
                request=request,
            )
        except HTTPException as exc:
            if exc.status_code != 400:
                raise
            error = str(exc.detail)
    context = build_new_search_context(
        state,
        request,
        results=results,
        error=error,
    )
    return catalog_response(
        "New.Index",
        **context,
        headers={"X-Robots-Tag": "noindex"},
    )


class RecursiveSection(BaseModel):
    section: Section
    search_query: str = ""
    sub_sections: list[RecursiveSection] = []


@router.get("/unit/{unit_id}", include_in_schema=False)
async def unit_detail(
    request: Request,
    unit_id: int,
    session: Annotated[AsyncSession, Depends(aget_session, scope="function")],
    meta_session: Annotated[AsyncSession, Depends(aget_meta_session, scope="function")],
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
            with tracer.start_as_current_span("section_paths"):
                section_paths = {
                    row.id: row
                    for row in (
                        await session.exec(
                            select(SectionPathView).where(
                                col(SectionPathView.id).in_(
                                    [section.id for section in sections]
                                )
                            )
                        )
                    ).all()
                }

            def offered_in_names(section: Section) -> list[str]:
                path = section_paths.get(section.id)
                value = (path.path_en or path.path_de) if path else None
                if value:
                    return value.split(" > ")

                return [section.name_english or section.name or ""]

            # create tree structure of offered in sections
            section_ids = {
                section.id: RecursiveSection(
                    section=section,
                    search_query=offered_in_query(offered_in_names(section)),
                )
                for section in sections
            }
            root_sections: list[RecursiveSection] = []
            for section in sections:
                if section.parent_id and section.parent_id in section_ids:
                    parent_section = section_ids[section.parent_id]
                    parent_section.sub_sections.append(section_ids[section.id])
                else:
                    root_sections.append(section_ids[section.id])

        with tracer.start_as_current_span("flagged") as span:
            flagged = (
                await meta_session.exec(
                    select(HTTPCache).where(
                        col(HTTPCache.url).contains(f"semkez={unit.semkez}"),
                        col(HTTPCache.url).contains(f"lerneinheitId={unit.id}"),
                        col(HTTPCache.flagged) == true(),
                    )
                )
            ).first()
            span.set_attribute("is_flagged", flagged is not None)

        with tracer.start_as_current_span("latest_semkez"):
            latest_semkez = (
                await session.exec(
                    select(LatestSemkez.semkez)
                    .order_by(col(LatestSemkez.id).desc())
                    .limit(1)
                )
            ).first()
            is_unpublished = False
            if latest_semkez is not None:
                is_unpublished = semkez_to_comparable(
                    unit.semkez
                ) > semkez_to_comparable(latest_semkez)
            span.set_attribute("is_unpublished", is_unpublished)

        # allows us to add canonical links to the newest unit
        newest_unit_id, _ = max(
            [(id, semkez_to_comparable(sk)) for id, sk in semkezs],
            key=lambda x: x[1],
        )

        with tracer.start_as_current_span("rating"):
            rating = None
            average_rating = "n/a"
            if unit.number:
                rating = await session.get(Rating, unit.number)
                average_rating = rating.average() if rating else "n/a"

        links = {
            str(request.url_for("unit_detail", unit_id=newest_unit_id)): "canonical"
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
            flagged=flagged is not None,
            is_unpublished=is_unpublished,
        )


@router.post("/unit/{unit_id}/flag", include_in_schema=False)
async def flag_unit(
    request: Request,
    unit_id: int,
    background_task: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(aget_session, scope="function")],
    meta_session: Annotated[AsyncSession, Depends(aget_meta_session, scope="function")],
):
    unit = await get_unit(unit_id, session)
    if not unit:
        return HTMLResponse(status_code=404)

    results = (
        await meta_session.exec(
            select(HTTPCache).where(
                col(HTTPCache.url).contains(f"semkez={unit.semkez}"),
                col(HTTPCache.url).contains(f"lerneinheitId={unit.id}"),
            )
        )
    ).all()

    for entry in results:
        entry.flagged = True
        meta_session.add(entry)

    await meta_session.commit()

    if Settings().flag_webhook:
        background_task.add_task(
            send_flagged_webhook,
            unit_id=unit_id,
        )

    base_url = str(request.url_for("unit_detail", unit_id=unit_id))
    return RedirectResponse(
        url=base_url,
        status_code=303,
    )


@router.get("/guide", include_in_schema=False)
async def guide():
    return catalog_response("Guide")


@router.get("/privacy", include_in_schema=False)
async def privacy():
    return catalog_response("Privacy")


@router.get("/{root}", include_in_schema=False)
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
        "llms.txt",
    ]:
        return HTMLResponse(status_code=404)

    if root == "sitemap.xml":
        generate_sitemap(Settings().sitemap_expiry)
        return FileResponse(
            Path(__file__).parents[1] / "static" / "sitemap" / "sitemap.xml",
            media_type="application/xml",
        )
    elif root == "robots.txt":
        robots_path = Path(__file__).parents[1] / "static" / "robots.txt"
        if robots_path.exists():
            return FileResponse(robots_path, media_type="text/plain")
        return HTMLResponse(status_code=404)

    root_path = Path(__file__).parents[1] / "static" / root
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


@router.get("/sitemap/{sitemap_file}", include_in_schema=False)
async def sitemap_files(sitemap_file: str):
    if re.match(r"sitemap(-\w+?)?\.xml", sitemap_file) is None:
        return HTMLResponse(status_code=404)
    sitemap_path = Path(__file__).parents[1] / "static" / "sitemap" / sitemap_file
    if sitemap_path.exists():
        return FileResponse(sitemap_path, media_type="application/xml")
    return HTMLResponse(status_code=404)


@router.get("/static/{file_path:path}", include_in_schema=False)
async def static_files(file_path: str):
    if file_path.startswith("components"):
        """
        Jinjax static files (JS/CSS) have the path of "/static/components/..."
        and are located in `api/templates` instead of in `api/static` like
        other static files.
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
    static_dir = Path(os.path.realpath(static_dir))
    requested_path = Path(os.path.realpath(static_dir / file_path.lstrip("/")))
    common_path = os.path.commonpath([static_dir, requested_path])
    if common_path != str(static_dir):
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

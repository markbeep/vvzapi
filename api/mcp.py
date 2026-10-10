"""MCP server for the VVZ API, served over streamable HTTP at `/mcp`.

The tools call the FastAPI endpoint functions in `api.routers` directly: no HTTP round trip, no
second service. Each tool opens one data-DB session and logs one line per call, so MCP traffic is
visible in the server log; searches are recorded in the analytics with `source="mcp"`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.streamable_http_manager import StreamableHTTPASGIApp
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field, JsonValue
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.routing import Route

from api.env import Settings
from api.models import Department, Level, Periodicity
from api.routers.v1 import courses, lecturers, misc, sections, units
from api.routers.v2.search import SearchResponse, run_search
from api.util.db import aget_session
from api.util.version import get_api_version

logger = logging.getLogger(__name__)

OrderBy = Literal[
    "title",
    "title_german",
    "title_english",
    "number",
    "credits",
    "year",
    "semester",
    "lecturer",
    "descriptions",
    "descriptions_german",
    "descriptions_english",
    "level",
    "department",
    "language",
    "offered",
    "examtype",
    "coursereview",
    "priority",
    "restricted",
    "primary_target_group",
]
UnitId = Annotated[
    int,
    Field(
        description="Learning unit id: the `id` of a unit, a value of `search_units`'s `semesters` map, "
        + "or an entry of `list_units`'s `unit_ids` (not the course number)."
    ),
]
LecturerId = Annotated[
    int,
    Field(
        description="Lecturer id from `get_unit_lecturers`, `get_unit_examiners` or `list_lecturers`."
    ),
]
SectionId = Annotated[
    int,
    Field(
        description="Catalogue section id from `get_unit_sections` or `list_sections`."
    ),
]

INSTRUCTIONS = """\
Tools for ETH Zurich's course catalogue (VVZ). Typical flow:
1. `search_units` to find courses (read the `vvzapi://search-syntax` resource before writing
   non-trivial queries; it documents the full query language).
2. `get_unit` for a course's full details, `get_unit_courses` for its times/places (Course rows),
   `get_unit_lecturers` / `get_unit_examiners` for lecturer ids, `get_unit_sections` for section ids.
3. `get_lecturer` to resolve a lecturer id to a name; `get_section` / `list_sections` to navigate
   the catalogue tree.

Id arguments are always named after the entity they identify - `unit_id`, `lecturer_id`,
`section_id`. No tool takes an argument called `id`:
- `unit_id` is the integer `id` of a learning unit: the values of `search_units`'s `semesters` map
  (semkez -> unit id) or the entries of `list_units`'s `unit_ids`.
- `lecturer_id` comes from `get_unit_lecturers`, `get_unit_examiners` or `list_lecturers`.
- `section_id` comes from `get_unit_sections` or `list_sections`.
Course numbers like `252-0027-00L` are strings: they belong in queries (`search_units`, or
`list_units`'s `number`), never in an id argument.

Semesters use the format `YYYY[S/W]` (e.g. `2026S`, `2025W`). A course number can exist in several
semesters: search results group units by number and give the semester -> unit id mapping."""

mcp: MCPServer[None] = MCPServer(
    "vvzapi",
    title="VVZ API (ETH Zurich course catalogue)",
    instructions=INSTRUCTIONS,
    version=get_api_version(),
)


@asynccontextmanager
async def _session() -> AsyncIterator[AsyncSession]:
    """One data-DB session per tool call, mirroring the endpoints' per-request dependency."""
    async for session in aget_session():
        yield session


@asynccontextmanager
async def _tool_call(what: str) -> AsyncIterator[None]:
    """Wrap one tool call: log a single line, and turn endpoint `HTTPException`s (unknown ids,
    unparsable queries) into readable tool errors."""
    started = time.perf_counter()
    try:
        try:
            yield
        except HTTPException as exc:
            raise ToolError(f"{what} failed: {exc.detail}") from exc
    finally:
        logger.info(
            "mcp %s (%d ms)", what, round((time.perf_counter() - started) * 1000)
        )


async def _call[T](what: str, endpoint: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Run one endpoint call on a fresh session."""
    async with _tool_call(what), _session() as session:
        return await endpoint(session)


def _found[T](record: T | None, what: str) -> T:
    """The `get_*` endpoints raise `HTTPException` for an unknown id rather than returning `None`."""
    if record is None:  # pragma: no cover - defensive: the endpoints raise instead
        raise ToolError(f"{what} not found")
    return record


def _transport_security() -> TransportSecuritySettings:
    """Reject requests whose Host/Origin is not this deployment's (DNS rebinding protection)."""
    base_url = Settings().base_url
    host = urlparse(base_url).netloc or "vvzapi.ch"
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            host,
            f"{host}:*",
            "127.0.0.1",
            "127.0.0.1:*",
            "localhost",
            "localhost:*",
        ],
        allowed_origins=[base_url],
    )


@asynccontextmanager
async def mcp_lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Run the MCP session manager (the lifespan of a mounted app is never entered)."""
    async with mcp.session_manager.run():
        yield


def mount_mcp(app: FastAPI) -> None:
    """Serve the MCP server at `/mcp`, with its tools calling `app`'s endpoints in-process.

    Must run before the `@app.get("/{root}")` catch-all is registered, or that route would
    answer `GET /mcp`.
    """
    app.mount(
        "/mcp",
        mcp.streamable_http_app(
            streamable_http_path="/", transport_security=_transport_security()
        ),
    )
    # Exact-path route: serve /mcp without Starlette's mount trailing-slash redirect.
    app.router.routes.append(
        Route("/mcp", endpoint=StreamableHTTPASGIApp(mcp.session_manager))
    )


def _summarize_search(response: SearchResponse) -> dict[str, JsonValue]:
    """Trim the search response to one compact record per course number."""
    results: list[JsonValue] = []
    for number, grouped in response.results.items():
        if not grouped.units:
            continue
        # semkez is YYYY + S/W, so lexicographic max == most recent semester.
        latest = max(grouped.units, key=lambda unit: unit.semkez)
        record: dict[str, JsonValue] = {
            "number": number,
            "title": latest.title,
            "title_english": latest.title_english,
            "credits": latest.credits,
            "levels": [level.value for level in latest.levels],
            "departments": [department.value for department in latest.departments],
            "language": latest.language,
            "rating": grouped.rating,
            "semesters": {unit.semkez: unit.id for unit in grouped.units},
        }
        results.append(record)
    return {
        "total": response.total,
        "results": results,
        "parsed_query": response.parsed_query,
        "exec_time_ms": response.exec_time_ms,
    }


# Tool returns are spelled `dict[str, JsonValue]` (never an alias): the SDK publishes a plain object
# schema only for a literal `dict[str, T]` annotation, and wraps every other return form in a
# `{"result": ...}` envelope.
@mcp.tool()
async def search_units(
    query: Annotated[
        str,
        Field(
            description='VVZ query, e.g. \'y:2026 s:fs o:"computer science master" o:"core course"\'. Plain text matches course titles. See the vvzapi://search-syntax resource.',
        ),
    ],
    limit: Annotated[
        int, Field(ge=1, le=100, description="Max course numbers per page.")
    ] = 20,
    offset: Annotated[int, Field(ge=0, description="Pagination offset.")] = 0,
    order_by: Annotated[OrderBy, Field(description="Sort field.")] = "year",
    order: Annotated[
        Literal["asc", "desc"], Field(description="Sort direction.")
    ] = "desc",
) -> dict[str, JsonValue]:
    """Search ETH Zurich courses by title, number, lecturer, programme, department, credits, semester or rating.

    Returns one compact record per course number: latest title(s), credits, levels, departments,
    language, CourseReview rating, and a `semesters` map of semkez -> learning unit id (pass those
    ids as `unit_id` to `get_unit` / `get_unit_courses`)."""
    what = f"search_units(query={query!r}, limit={limit}, offset={offset})"
    async with _tool_call(what):
        response = await run_search(
            query,
            offset=offset,
            limit=limit,
            order_by=order_by,
            order=order,
            source="mcp",
            view="api",
            page=(offset // limit) + 1,
        )
    return _summarize_search(response)


@mcp.tool()
async def get_unit(unit_id: UnitId) -> dict[str, JsonValue]:
    """Full details for one learning unit (course) selected by `unit_id`: titles, credits,
    descriptions, objectives, exam info, sign-up dates, restrictions, groups, and more."""
    unit = await _call(
        f"get_unit(unit_id={unit_id})",
        lambda session: units.get_unit(unit_id=unit_id, session=session),
    )
    return _found(unit, f"unit_id {unit_id}").model_dump(mode="json")


@mcp.tool()
async def get_unit_courses(unit_id: UnitId) -> dict[str, JsonValue]:
    """The scheduled courses (times, places, hours, type) of the learning unit `unit_id`."""
    rows = await _call(
        f"get_unit_courses(unit_id={unit_id})",
        lambda session: courses.get_courses(unit_id=unit_id, session=session),
    )
    return {
        "unit_id": unit_id,
        "courses": [course.model_dump(mode="json") for course in rows],
    }


@mcp.tool()
async def get_unit_sections(unit_id: UnitId) -> dict[str, JsonValue]:
    """Ids of the catalogue sections the learning unit `unit_id` is listed under; resolve them with
    `get_section`."""
    rows = await _call(
        f"get_unit_sections(unit_id={unit_id})",
        lambda session: units.get_unit_sections(unit_id=unit_id, session=session),
    )
    return {"unit_id": unit_id, "section_ids": list(rows)}


@mcp.tool()
async def get_unit_lecturers(unit_id: UnitId) -> dict[str, JsonValue]:
    """Ids of the lecturers of the learning unit `unit_id`; resolve them with `get_lecturer`."""
    rows = await _call(
        f"get_unit_lecturers(unit_id={unit_id})",
        lambda session: units.get_unit_lecturers(unit_id=unit_id, session=session),
    )
    return {"unit_id": unit_id, "lecturer_ids": list(rows)}


@mcp.tool()
async def get_unit_examiners(unit_id: UnitId) -> dict[str, JsonValue]:
    """Ids of the examiners of the learning unit `unit_id`; resolve them with `get_lecturer`."""
    rows = await _call(
        f"get_unit_examiners(unit_id={unit_id})",
        lambda session: units.get_unit_examiners(unit_id=unit_id, session=session),
    )
    return {"unit_id": unit_id, "lecturer_ids": list(rows)}


@mcp.tool()
async def list_units(
    limit: Annotated[int, Field(ge=1, le=1000)] = 100,
    offset: Annotated[int, Field(ge=0)] = 0,
    semkez: Annotated[str | None, Field(description="Semester, e.g. 2025W.")] = None,
    level: Annotated[Level | None, Field(description="Course level.")] = None,
    department: Annotated[
        Department | None,
        Field(description="ETH department id (5 = Computer Science)."),
    ] = None,
    section: Annotated[
        int | None, Field(description="Section id to restrict to.")
    ] = None,
    number: Annotated[str | None, Field(description="Course number (partial).")] = None,
    title: Annotated[
        str | None, Field(description="Substring of the German or English title.")
    ] = None,
    lecturer_id: Annotated[int | None, Field(description="Lecturer id.")] = None,
    lecturer_name: Annotated[
        str | None, Field(description="Lecturer first name.")
    ] = None,
    lecturer_surname: Annotated[
        str | None, Field(description="Lecturer surname.")
    ] = None,
    unit_type: Annotated[
        str | None, Field(description="Unit type: O, W+, W, E-, Z, Dr, ...")
    ] = None,
    language: Annotated[
        str | None, Field(description="Language of instruction.")
    ] = None,
    periodicity: Annotated[
        Periodicity | None,
        Field(description="0=once, 1=annual, 2=semester, 3=biennial."),
    ] = None,
    ects_min: Annotated[
        float | None, Field(description="Minimum ECTS credits.")
    ] = None,
    ects_max: Annotated[
        float | None, Field(description="Maximum ECTS credits.")
    ] = None,
    content_search: Annotated[
        str | None, Field(description="Substring of the catalogue data.")
    ] = None,
) -> dict[str, JsonValue]:
    """List learning unit ids matching VVZ-style filters (useful for `unit_type`/`periodicity`,
    which the search query language does not cover). Pass an id as `unit_id` to `get_unit`."""
    rows = await _call(
        f"list_units(semkez={semkez}, level={level}, department={department}, periodicity={periodicity})",
        lambda session: units.list_units(
            session=session,
            limit=limit,
            offset=offset,
            semkez=semkez,
            level=level,
            department=department,
            section=section,
            number=number,
            title=title,
            lecturer_id=lecturer_id,
            lecturer_name=lecturer_name,
            lecturer_surname=lecturer_surname,
            type=unit_type,
            language=language,
            periodicity=periodicity,
            ects_min=ects_min,
            ects_max=ects_max,
            content_search=content_search,
        ),
    )
    return {"unit_ids": list(rows), "limit": limit, "offset": offset}


@mcp.tool()
async def get_lecturer(lecturer_id: LecturerId) -> dict[str, JsonValue]:
    """Name, title and department of the lecturer `lecturer_id`."""
    person = await _call(
        f"get_lecturer(lecturer_id={lecturer_id})",
        lambda session: lecturers.get_lecturer(
            lecturer_id=lecturer_id, session=session
        ),
    )
    return _found(person, f"lecturer_id {lecturer_id}").model_dump(mode="json")


@mcp.tool()
async def list_lecturers(
    limit: Annotated[int, Field(ge=1, le=1000)] = 100,
    offset: Annotated[int, Field(ge=0)] = 0,
) -> dict[str, JsonValue]:
    """Page through lecturers (pass an id as `lecturer_id` to `get_lecturer`), ordered by id."""
    rows = await _call(
        f"list_lecturers(limit={limit}, offset={offset})",
        lambda session: lecturers.list_lecturers(
            session=session, limit=limit, offset=offset
        ),
    )
    return {
        "lecturers": [person.model_dump(mode="json") for person in rows],
        "limit": limit,
        "offset": offset,
    }


@mcp.tool()
async def list_sections(
    limit: Annotated[int, Field(ge=1, le=1000)] = 100,
    offset: Annotated[int, Field(ge=0)] = 0,
    semkez: Annotated[str | None, Field(description="Semester, e.g. 2025W.")] = None,
    level: Annotated[int | None, Field(description="Section level.")] = None,
    name_search: Annotated[
        str | None, Field(description="Substring of section names.")
    ] = None,
    comment_search: Annotated[
        str | None, Field(description="Substring of section comments.")
    ] = None,
    parent_id: Annotated[
        int | None,
        Field(description="Restrict to the direct children of this section id."),
    ] = None,
    sort_lex: Annotated[
        bool, Field(description="Sort alphabetically as on VVZ instead of by id.")
    ] = False,
) -> dict[str, JsonValue]:
    """List catalogue section ids matching filters; pass an id as `section_id` to `get_section`."""
    rows = await _call(
        f"list_sections(semkez={semkez}, level={level}, parent_id={parent_id})",
        lambda session: sections.list_sections(
            session=session,
            limit=limit,
            offset=offset,
            semkez=semkez,
            level=level,
            name_search=name_search,
            comment_search=comment_search,
            parent_id=parent_id,
            sort_lex=sort_lex,
        ),
    )
    return {"section_ids": list(rows), "limit": limit, "offset": offset}


@mcp.tool()
async def get_section(section_id: SectionId) -> dict[str, JsonValue]:
    """The catalogue section `section_id`, with its parent/child sections and the learning units it
    contains."""
    section = await _call(
        f"get_section(section_id={section_id})",
        lambda session: sections.get_section(session=session, section_id=section_id),
    )
    return _found(section, f"section_id {section_id}").model_dump(mode="json")


@mcp.tool()
async def list_semesters() -> dict[str, JsonValue]:
    """All semesters (YYYY[S/W] with S=spring, W=autumn) that have learning units available."""
    rows = await _call(
        "list_semesters", lambda session: misc.list_semesters(session=session)
    )
    return {"semesters": list(rows)}


_SYNTAX_GUIDE = Path(__file__).resolve().parent / "static" / "llms.txt"


@mcp.resource(
    "vvzapi://search-syntax",
    name="VVZ search syntax",
    description="Full guide to the VVZ query language accepted by search_units.",
    mime_type="text/markdown",
)
def search_syntax() -> str:
    """Read the VVZ search query syntax guide."""
    try:
        return _SYNTAX_GUIDE.read_text(encoding="utf-8")
    except OSError:
        return (
            "Search syntax guide unavailable. Plain text matches course titles; use key:value "
            'filters such as y:2026, s:fs, o:"program name", lecturer:"surname", c>=10.'
        )

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypedDict
from urllib.parse import urlencode

from fastapi import Request

from api.models import Department, Level
from api.routers.v0.search import SearchResponse
from api.util.parse_query import QueryKey, offered_in_query
from api.util.section_filters import SectionFilterData, get_section_filter_data

type SortKey = Literal["title", "number", "credits", "latest", "coursereview"]
type SortDirection = Literal["asc", "desc"]

SORT_ORDER: dict[SortKey, SortDirection] = {
    "title": "asc",
    "number": "asc",
    "credits": "desc",
    "latest": "desc",
    "coursereview": "desc",
}
SORT_ORDER_BY: dict[SortKey, QueryKey] = {
    "title": "title_english",
    "number": "number",
    "credits": "credits",
    "latest": "year",
    "coursereview": "coursereview",
}
SORT_KEYS: tuple[SortKey, ...] = ("title", "credits", "latest", "coursereview")
FILTER_KEYS = {
    "program",
    "section",
    "newest",
    "semester",
    "level",
    "dept",
    "min_credits",
    "min_rating",
}


@dataclass(frozen=True)
class NewSearchState:
    q: str
    program: int | None
    section: int | None
    newest: bool
    semesters: tuple[str, ...]
    levels: tuple[str, ...]
    depts: tuple[str, ...]
    min_credits: int | None
    min_rating: float | None
    sort: SortKey
    order: SortDirection
    limit: int
    page: int
    section_data: SectionFilterData
    order_by: QueryKey


class SearchChip(TypedDict):
    label: str
    href: str


class SortLink(TypedDict):
    href: str
    active: bool
    aria: Literal["ascending", "descending"]
    arrow: Literal["up", "down", ""]


class NewSearchContext(TypedDict):
    q: str
    results: SearchResponse | None
    error: str | None
    page: int
    limit: int
    total: int
    result_from: int
    to: int
    pages: int
    exec_time_ms: float
    section_data: SectionFilterData
    latest_semester: str | None
    selected_programme: int | None
    selected_section: int | None
    newest: bool
    selected_semesters: tuple[str, ...]
    selected_levels: tuple[str, ...]
    selected_depts: tuple[str, ...]
    min_credits: int | None
    min_rating: float | None
    sort: SortKey
    order: SortDirection
    direction_label: str
    sort_links: dict[SortKey, SortLink]
    toggle_order_url: str
    limits: tuple[int, ...]
    sort_options: tuple[tuple[SortKey, str], ...]
    levels: tuple[str, ...]
    departments: tuple[tuple[str, str, str], ...]
    semesters: tuple[tuple[str, str], ...]
    chips: list[SearchChip]
    active_count: int
    clear_url: str
    prev_url: str | None
    next_url: str | None


def _fmt_sem(sem: str) -> str:
    return f"{sem[:4]} {sem[4:]}"


def _quote_value(value: str) -> str:
    if '"' not in value:
        return f'"{value}"'
    if "`" not in value:
        return f"`{value}`"
    return '"' + value.replace('"', '\\"') + '"'


def _or_terms(key: str, values: tuple[str, ...], *, quote: bool = False) -> str:
    if not values:
        return ""
    rendered = [f"{key}:{_quote_value(value) if quote else value}" for value in values]
    return rendered[0] if len(rendered) == 1 else "(" + " OR ".join(rendered) + ")"


def compose_query(state: NewSearchState) -> str:
    parts: list[str] = []
    if state.q:
        parts.append(state.q)
    offered = offered_in_query(state.section_data.path_names)
    if offered:
        parts.append(offered)
    if state.newest and state.section_data.latest_semester:
        parts.append(f"semkez:{state.section_data.latest_semester}")
    semester = _or_terms("semester", state.semesters)
    if semester:
        parts.append(semester)
    level = _or_terms("level", state.levels)
    if level:
        parts.append(level)
    if state.depts:
        depts = tuple(str(Department(int(dept))) for dept in state.depts)
        parts.append(_or_terms("department", depts, quote=True))
    if state.min_credits is not None:
        parts.append(f"credits>={state.min_credits}")
    if state.min_rating is not None:
        parts.append(f"coursereview>={state.min_rating}")
    return " ".join(parts)


async def build_new_search_state(
    *,
    q: str,
    program: int,
    section: int,
    newest: bool,
    semesters: Sequence[str],
    levels: Sequence[str],
    depts: Sequence[str],
    min_credits: int,
    min_rating: float,
    sort: SortKey,
    order: SortDirection | None,
    limit: int,
    page: int,
) -> NewSearchState:
    program_id = program or None
    section_id = section or None
    section_data = await get_section_filter_data(program_id, section_id)
    selected_program = (
        section_data.selected_programme.id if section_data.selected_programme else None
    )
    selected_section = (
        section_data.selected_section.id if section_data.selected_section else None
    )

    semester_values = tuple(
        value for value in (v.upper() for v in semesters) if value in {"W", "S"}
    )
    level_order = {level.value for level in Level}
    level_values = tuple(
        value for value in (v.upper() for v in levels) if value in level_order
    )
    dept_order = {str(dept.value) for dept in Department}
    dept_values = tuple(dept for dept in depts if dept in dept_order)

    sort_value: SortKey = sort if sort in SORT_ORDER else "title"
    order_value: SortDirection = (
        "asc"
        if order == "asc"
        else "desc"
        if order == "desc"
        else SORT_ORDER[sort_value]
    )
    limit_value = limit if limit in {20, 40, 60, 80, 100} else 20
    page_value = max(1, page)

    return NewSearchState(
        q=q.strip(),
        program=selected_program,
        section=selected_section,
        newest=newest,
        semesters=semester_values,
        levels=level_values,
        depts=dept_values,
        min_credits=min_credits or None,
        min_rating=min_rating or None,
        sort=sort_value,
        order=order_value,
        limit=limit_value,
        page=page_value,
        section_data=section_data,
        order_by=SORT_ORDER_BY[sort_value],
    )


def _url_with(
    request: Request,
    *,
    updates: dict[str, str] | None = None,
) -> str:
    updates = updates or {}
    items: list[tuple[str, str]] = []
    for key, value in request.query_params.multi_items():
        if key == "page" or key in updates:
            continue
        items.append((key, value))
    items.extend(updates.items())
    return "/new?" + urlencode(items)


def _url_without(
    request: Request,
    *,
    keys: set[str] | None = None,
    values: set[tuple[str, str]] | None = None,
    page: int | None = None,
    keep_filters: bool = True,
) -> str:
    keys = keys or set()
    values = values or set()
    items: list[tuple[str, str]] = []
    for key, value in request.query_params.multi_items():
        if key == "page":
            continue
        if not keep_filters and key in FILTER_KEYS:
            continue
        if key in keys:
            continue
        if (key, value) in values:
            continue
        items.append((key, value))
    if page is not None:
        items.append(("page", str(page)))
    return "/new?" + urlencode(items)


def _direction_label(sort: SortKey, order: SortDirection) -> str:
    if sort == "title":
        return "A–Z" if order == "asc" else "Z–A"
    if sort == "number":
        return "Ascending" if order == "asc" else "Descending"
    if sort == "credits":
        return "Most ECTS" if order == "desc" else "Fewest ECTS"
    if sort == "latest":
        return "Newest first" if order == "desc" else "Oldest first"
    return "Highest rated" if order == "desc" else "Lowest rated"


def build_new_search_context(
    state: NewSearchState,
    request: Request,
    *,
    results: SearchResponse | None,
    error: str | None,
) -> NewSearchContext:
    section_data = state.section_data
    active_count = (
        (1 if section_data.active_label else 0)
        + (1 if state.newest else 0)
        + len(state.semesters)
        + len(state.levels)
        + len(state.depts)
        + (1 if state.min_credits is not None else 0)
        + (1 if state.min_rating is not None else 0)
    )

    chips: list[SearchChip] = []
    if section_data.active_label:
        chips.append(
            {
                "label": f"Offered in: {section_data.active_label}",
                "href": _url_without(request, keys={"program", "section"}),
            }
        )
    if state.newest and section_data.latest_semester:
        chips.append(
            {
                "label": f"Newest offering ({_fmt_sem(section_data.latest_semester)})",
                "href": _url_without(request, keys={"newest"}),
            }
        )
    for semester in state.semesters:
        chips.append(
            {
                "label": "Autumn" if semester == "W" else "Spring",
                "href": _url_without(request, values={("semester", semester)}),
            }
        )
    for level in state.levels:
        chips.append(
            {
                "label": level,
                "href": _url_without(request, values={("level", level)}),
            }
        )
    for dept in state.depts:
        department = Department(int(dept))
        chips.append(
            {
                "label": f"{department.short()} · {department}",
                "href": _url_without(request, values={("dept", dept)}),
            }
        )
    if state.min_credits is not None:
        chips.append(
            {
                "label": f"{state.min_credits}+ ECTS",
                "href": _url_without(request, keys={"min_credits"}),
            }
        )
    if state.min_rating is not None:
        chips.append(
            {
                "label": f"CR {state.min_rating:.1f}+",
                "href": _url_without(request, keys={"min_rating"}),
            }
        )

    sort_links: dict[SortKey, SortLink] = {}
    for key in SORT_KEYS:
        active = state.sort == key
        next_order = (
            ("desc" if state.order == "asc" else "asc") if active else SORT_ORDER[key]
        )
        sort_links[key] = {
            "href": _url_with(
                request,
                updates={"sort": key, "order": next_order},
            ),
            "active": active,
            "aria": "ascending" if state.order == "asc" else "descending",
            "arrow": ("up" if state.order == "asc" else "down") if active else "",
        }
    toggle_order = "desc" if state.order == "asc" else "asc"

    total = results.total if results else 0
    exec_time_ms = results.exec_time_ms if results else 0.0
    pages = max(1, (total + state.limit - 1) // state.limit)
    start = (state.page - 1) * state.limit
    return {
        "q": state.q,
        "results": results,
        "error": error,
        "page": state.page,
        "limit": state.limit,
        "total": total,
        "result_from": start + 1 if total else 0,
        "to": min(start + state.limit, total),
        "pages": pages,
        "exec_time_ms": exec_time_ms,
        "section_data": section_data,
        "latest_semester": section_data.latest_semester,
        "selected_programme": state.program,
        "selected_section": state.section,
        "newest": state.newest,
        "selected_semesters": state.semesters,
        "selected_levels": state.levels,
        "selected_depts": state.depts,
        "min_credits": state.min_credits,
        "min_rating": state.min_rating,
        "sort": state.sort,
        "order": state.order,
        "direction_label": _direction_label(state.sort, state.order),
        "sort_links": sort_links,
        "toggle_order_url": _url_with(
            request,
            updates={"sort": state.sort, "order": toggle_order},
        ),
        "limits": (20, 40, 60, 80, 100),
        "sort_options": (
            ("title", "Alphabetical"),
            ("number", "Number"),
            ("credits", "ECTS"),
            ("latest", "Latest offering"),
            ("coursereview", "CourseReview rating"),
        ),
        "levels": tuple(level.value for level in Level),
        "departments": tuple(
            (str(dept.value), str(dept), dept.short()) for dept in Department
        ),
        "semesters": (("W", "Autumn"), ("S", "Spring")),
        "chips": chips,
        "active_count": active_count,
        "clear_url": _url_without(request, keep_filters=False),
        "prev_url": (
            _url_without(request, page=state.page - 1) if state.page > 1 else None
        ),
        "next_url": (
            _url_without(request, page=state.page + 1) if state.page < pages else None
        ),
    }

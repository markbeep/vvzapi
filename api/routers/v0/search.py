import asyncio
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass
from enum import StrEnum
from timeit import default_timer
from typing import Annotated, Any, Literal, overload, override

from fastapi import APIRouter, HTTPException, Query, Request
from opentelemetry import trace
from pydantic import BaseModel, Field
from pyparsing import ParseException
from sqlalchemy.orm import load_only
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement
from sqlmodel import (
    Integer,
    String,
    and_,
    col,
    distinct,
    func,
    not_,
    or_,
    select,
)
from sqlmodel import (
    cast as sql_cast,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar
from starlette.status import HTTP_400_BAD_REQUEST

from api.analytics.events import (
    boolean_shape,
    categorize_query,
    classify_client_for_request,
    collect_stages,
    observe_stage,
    query_filters,
    record_search,
)
from api.analytics.prometheus import (
    SEARCH_DURATION,
    SEARCH_FILTER_USED,
    SEARCH_REQUESTS,
    SEARCH_RESULT_COUNT,
    SEARCH_ZERO_RESULTS,
)
from api.models import (
    Department,
    LearningUnit,
    Lecturer,
    Level,
    Rating,
    SectionPathView,
    UnitDepartmentView,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
)
from api.util.db import aengine
from api.util.parse_query import (
    AND,
    OR,
    FilterOperator,
    Operator,
    QueryKey,
    build_search_operators,
)
from api.util.pydantic_type import Int64
from api.util.semkez import semkez_to_comparable

router = APIRouter(prefix="/search", tags=["Search"])

tracer = trace.get_tracer(__name__)


class GroupedLearningUnits(BaseModel):
    number: str
    units: list[LearningUnit]
    rating: float | None = None

    @property
    def semkezs(self) -> list[str]:
        return sorted({unit.semkez for unit in self.units if unit.semkez})

    def latest_unit(self) -> LearningUnit | None:
        if not self.units:
            return None
        return max(self.units, key=lambda unit: semkez_to_comparable(unit.semkez))

    def with_semkez(self, semkez: str) -> LearningUnit | None:
        for unit in self.units:
            if unit.semkez == semkez:
                return unit
        return None

    @override
    def __iter__(self):
        for unit in sorted(
            self.units,
            key=lambda u: semkez_to_comparable(u.semkez),
            reverse=True,
        ):
            yield unit.semkez, unit


class SearchResultView(StrEnum):
    """How much data a search materializes and returns."""

    full = "full"
    compact = "compact"
    numbers = "numbers"
    ids = "ids"


class CompactLearningUnit(BaseModel):
    """One matching course number, described by its most recent learning unit."""

    number: str = Field(description="Course number, e.g. `252-0027-00L`.")
    title: str | None = Field(
        default=None, description="German title of the most recent unit."
    )
    title_english: str | None = Field(
        default=None, description="English title of the most recent unit."
    )
    credits: float | None = Field(default=None, description="ECTS credits.")
    levels: list[Level] = Field(
        default_factory=list, description="Degree-program levels, e.g. `BSC`, `MSC`."
    )
    departments: list[Department] = Field(
        default_factory=list, description="Offering departments as numeric ids."
    )
    language: str | None = Field(
        default=None, description="Language the unit is taught in."
    )
    rating: float | None = Field(
        default=None, description="Combined CourseReview average, if rated."
    )
    semesters: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Semester (`semkez`) to learning unit id, newest first. Pass an id to "
            "`/api/v1/unit/{unit_id}/get` for the full record."
        ),
    )


class SearchResponse(BaseModel):
    total: int = Field(
        description="Total amount of matching course numbers, not just those on this page."
    )
    results: dict[str, GroupedLearningUnits] = Field(
        description="Course number to all of its learning units across semesters."
    )
    parsed_query: str = Field(description="How the query was interpreted.")
    exec_time_ms: float = Field(description="Time spent executing the search.")

    @override
    def __iter__(self) -> Generator[tuple[str, GroupedLearningUnits]]:
        yield from self.results.items()


class CompactSearchResponse(BaseModel):
    total: int = Field(
        description="Total amount of matching course numbers, not just those on this page."
    )
    results: list[CompactLearningUnit] = Field(
        description="One summary per course number, in page order."
    )
    parsed_query: str = Field(description="How the query was interpreted.")
    exec_time_ms: float = Field(description="Time spent executing the search.")


class NumbersResponse(BaseModel):
    total: int = Field(
        description="Total amount of matching course numbers, not just those on this page."
    )
    results: list[str] = Field(
        description="Matching course numbers in page order, e.g. `252-0027-00L`."
    )
    parsed_query: str = Field(description="How the query was interpreted.")
    exec_time_ms: float = Field(description="Time spent executing the search.")


class IdsResponse(BaseModel):
    total: int = Field(
        description="Total number of matching learning units, not just those on this page."
    )
    results: list[int] = Field(
        description=(
            "Matching learning unit ids in `order_by` order. Each id is a unit that "
            "matches the query itself; pass it to `/api/v1/unit/{unit_id}/get` for the "
            "full record."
        )
    )
    parsed_query: str = Field(description="How the query was interpreted.")
    exec_time_ms: float = Field(description="Time spent executing the search.")


@dataclass
class SearchMatch:
    """Materialized search results; exactly one representation field is set."""

    count: int
    filters_used: AND | OR
    full: dict[str, GroupedLearningUnits] | None = None
    compact: list[CompactLearningUnit] | None = None
    numbers: list[str] | None = None
    ids: list[int] | None = None


type SearchResponseUnion = (
    SearchResponse | CompactSearchResponse | NumbersResponse | IdsResponse
)


_COMPACT_LOAD_ATTRIBUTES = (
    LearningUnit.id,
    LearningUnit.number,
    LearningUnit.semkez,
    LearningUnit.title,
    LearningUnit.title_english,
    LearningUnit.credits,
    LearningUnit.levels,
    LearningUnit.departments,
    LearningUnit.language,
)


def _compact_load_option():
    # SQLModel annotates fields as their Python values (int, str, ...), which does not
    # satisfy SQLAlchemy's QueryableAttribute typing. The values are mapped attributes
    # at runtime; keep this tuple in sync with CompactLearningUnit.
    return load_only(*_COMPACT_LOAD_ATTRIBUTES)  # pyright: ignore[reportArgumentType]


def _build_boolean_clause(op: AND | OR):
    with tracer.start_as_current_span("build_boolean_clause") as span:
        booleans: list[BinaryExpression[bool] | ColumnElement[bool]] = []
        filters_used = OR(ops=[]) if isinstance(op, OR) else AND(ops=[])

        offered_in_names: set[str] = set()
        not_offered_in_names: set[str] = set()
        for filter_ in op.ops:
            if isinstance(filter_, (AND, OR)):
                clause, used_filters = _build_boolean_clause(filter_)
                booleans.append(clause)
                filters_used.ops.append(used_filters)
                continue
            match filter_.key:
                case "title_german":
                    clause = col(LearningUnit.title).contains(filter_.value)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "title_english":
                    clause = col(LearningUnit.title_english).contains(filter_.value)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "title":
                    clause = or_(
                        func.coalesce(LearningUnit.title, "").contains(filter_.value),
                        func.coalesce(LearningUnit.title_english, "").contains(
                            filter_.value
                        ),
                    )
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "number":
                    clause = col(LearningUnit.number).contains(filter_.value)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "credits":
                    try:
                        ects_value = float(filter_.value)
                    except ValueError:
                        continue
                    match filter_.operator:
                        case Operator.eq:
                            booleans.append(col(LearningUnit.credits) == ects_value)
                        case Operator.ne:
                            booleans.append(col(LearningUnit.credits) != ects_value)
                        case Operator.gt:
                            booleans.append(col(LearningUnit.credits) > ects_value)
                        case Operator.lt:
                            booleans.append(col(LearningUnit.credits) < ects_value)
                        case Operator.ge:
                            booleans.append(col(LearningUnit.credits) >= ects_value)
                        case Operator.le:
                            booleans.append(col(LearningUnit.credits) <= ects_value)
                    filters_used.ops.append(filter_)
                case "year":
                    if not filter_.value.isdigit():
                        continue
                    year_value = int(filter_.value)
                    match filter_.operator:
                        case Operator.eq:
                            booleans.append(
                                func.substr(LearningUnit.semkez, 1, 4)
                                == str(year_value)
                            )
                        case Operator.ne:
                            booleans.append(
                                func.substr(LearningUnit.semkez, 1, 4)
                                != str(year_value)
                            )
                        case Operator.gt:
                            booleans.append(
                                func.substr(LearningUnit.semkez, 1, 4) > str(year_value)
                            )
                        case Operator.lt:
                            booleans.append(
                                func.substr(LearningUnit.semkez, 1, 4) < str(year_value)
                            )
                        case Operator.ge:
                            booleans.append(
                                func.substr(LearningUnit.semkez, 1, 4)
                                >= str(year_value)
                            )
                        case Operator.le:
                            booleans.append(
                                func.substr(LearningUnit.semkez, 1, 4)
                                <= str(year_value)
                            )
                    filters_used.ops.append(filter_)
                case "semester":
                    if len(filter_.value) == 0 or filter_.value[0].upper() not in [
                        "S",
                        "W",
                        "F",
                        "H",
                    ]:
                        continue
                    sem_filter = filter_.value[0].upper()
                    if sem_filter == "F":  # fs
                        sem_filter = "S"
                    elif sem_filter == "H":  # hs
                        sem_filter = "W"
                    if filter_.operator == Operator.ne:
                        booleans.append(
                            func.substr(LearningUnit.semkez, 5, 1) != sem_filter
                        )
                    else:
                        booleans.append(
                            func.substr(LearningUnit.semkez, 5, 1) == sem_filter
                        )
                    filters_used.ops.append(
                        FilterOperator(
                            operator=filter_.operator,
                            key=filter_.key,
                            value="FS" if sem_filter == "S" else "HS",
                        )
                    )
                case "lecturer":
                    clause = or_(
                        func.concat(Lecturer.name, " ", Lecturer.surname).like(
                            f"%{filter_.value}%"
                        ),
                        func.concat(Lecturer.surname, " ", Lecturer.name).like(
                            f"%{filter_.value}%"
                        ),
                    )
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "descriptions_german":
                    clause = or_(
                        (
                            func.coalesce(LearningUnit.content, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.literature, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.objective, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.lecture_notes, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.additional, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.comment, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.abstract, "").contains(
                                filter_.value
                            )
                        ),
                    )
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "descriptions_english":
                    clause = or_(
                        (
                            func.coalesce(LearningUnit.content_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.literature_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.objective_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(
                                LearningUnit.lecture_notes_english, ""
                            ).contains(filter_.value)
                        ),
                        (
                            func.coalesce(LearningUnit.additional_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.comment_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.abstract_english, "").contains(
                                filter_.value
                            )
                        ),
                    )
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "descriptions":
                    clause = or_(
                        (
                            func.coalesce(LearningUnit.content, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.content_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.literature, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.literature_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.objective, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.objective_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.lecture_notes, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(
                                LearningUnit.lecture_notes_english, ""
                            ).contains(filter_.value)
                        ),
                        (
                            func.coalesce(LearningUnit.additional, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.additional_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.comment, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.comment_english, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.abstract, "").contains(
                                filter_.value
                            )
                        ),
                        (
                            func.coalesce(LearningUnit.abstract_english, "").contains(
                                filter_.value
                            )
                        ),
                    )
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "department":
                    closest_dept = Department.closest_match(filter_.value)
                    if not closest_dept:
                        continue
                    subquery = select(UnitDepartmentView.unit_id).where(
                        UnitDepartmentView.department_id == closest_dept.value
                    )
                    clause = col(LearningUnit.id).in_(subquery)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(
                        FilterOperator(
                            key=filter_.key,
                            operator=filter_.operator,
                            value=str(closest_dept),
                        )
                    )
                case "level":
                    clause = col(LearningUnit.levels).contains(filter_.value)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(
                        FilterOperator(
                            key=filter_.key,
                            operator=filter_.operator,
                            value=filter_.value.upper(),
                        )
                    )
                case "language":
                    clause = col(LearningUnit.language).contains(filter_.value)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "offered":
                    if filter_.operator == Operator.ne:
                        not_offered_in_names.add(filter_.value)
                    else:
                        offered_in_names.add(filter_.value)
                    filters_used.ops.append(filter_)
                case "examtype":
                    clause = col(LearningUnit.exam_type).contains(filter_.value)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "coursereview":
                    average_rating = (
                        col(Rating.recommended)
                        + col(Rating.engaging)
                        + col(Rating.difficulty)
                        + col(Rating.effort)
                        + col(Rating.resources)
                    ) / 5
                    try:
                        rating_value = float(filter_.value)
                    except ValueError:
                        continue
                    match filter_.operator:
                        case Operator.eq:
                            booleans.append(average_rating == rating_value)
                        case Operator.ne:
                            booleans.append(average_rating != rating_value)
                        case Operator.gt:
                            booleans.append(average_rating > rating_value)
                        case Operator.lt:
                            booleans.append(average_rating < rating_value)
                        case Operator.ge:
                            booleans.append(average_rating >= rating_value)
                        case Operator.le:
                            booleans.append(average_rating <= rating_value)
                    filters_used.ops.append(filter_)
                case "priority":
                    clause = col(LearningUnit.priority).contains(filter_.value)
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "primary_target_group":
                    clause = col(LearningUnit.primary_target_group).contains(
                        filter_.value
                    )
                    if filter_.operator == Operator.ne:
                        clause = not_(clause)
                    booleans.append(clause)
                    filters_used.ops.append(filter_)
                case "restricted":
                    restricted = filter_.value.lower() in {"true", "yes", "1", "y", "t"}
                    if not restricted and filter_.value.lower() not in {
                        "false",
                        "no",
                        "0",
                        "n",
                        "f",
                    }:
                        continue
                    if filter_.operator == Operator.ne:
                        restricted = not restricted
                    if restricted:
                        booleans.append(col(LearningUnit.priority).is_not(None))
                    else:
                        booleans.append(col(LearningUnit.priority).is_(None))
                    filters_used.ops.append(filter_)

        # matches all filters
        if offered_in_names:
            clauses = (
                col(SectionPathView.path_en).contains(name)
                | col(SectionPathView.path_de).contains(name)
                for name in offered_in_names
            )
            if isinstance(op, OR):
                clauses = or_(*clauses)
            else:
                clauses = and_(*clauses)
            booleans.append(clauses)
        if not_offered_in_names:
            clauses = (
                col(SectionPathView.path_en).contains(name)
                | col(SectionPathView.path_de).contains(name)
                for name in not_offered_in_names
            )
            if isinstance(op, OR):
                clauses = or_(*clauses)
            else:
                clauses = and_(*clauses)
            booleans.append(not_(clauses))

        span.set_attribute("num_filters", len(filters_used.ops))
        span.set_attribute("num_db_filters", len(booleans))
        span.set_attribute("filter_keys", str(filters_used))

        if len(booleans) == 0:
            raise ValueError("No valid filters found")

        if isinstance(op, AND):
            return and_(*booleans), filters_used
        else:
            return or_(*booleans), filters_used


async def match_filters(
    filters: AND | OR,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    descending: bool = True,
    result_view: SearchResultView = SearchResultView.full,
) -> SearchMatch:
    with tracer.start_as_current_span("match_filters") as span:
        span.set_attribute("offset", offset)
        span.set_attribute("limit", limit)
        span.set_attribute("order_by", order_by)
        span.set_attribute("descending", descending)
        span.set_attribute("result_view", result_view.value)

        # query to perform the initial filtering
        query = select(
            LearningUnit,
            year := sql_cast(func.substr(LearningUnit.semkez, 1, 4), Integer),
            semester := sql_cast(func.substr(LearningUnit.semkez, 5, 1), String),
        )
        # secondary query that will be used to return the sorted values
        final_query = select(LearningUnit)

        #########
        # Joins #
        #########
        if any(f.key == "lecturer" for f in filters) or order_by == "lecturer":

            def join_lecturer[T: Select[Any, Any, Any] | SelectOfScalar[Any]](
                q: T,
            ) -> T:
                return (
                    q.join(
                        UnitExaminerLink,
                        onclause=col(LearningUnit.id) == UnitExaminerLink.unit_id,
                    )
                    .join(
                        UnitLecturerLink,
                        onclause=col(LearningUnit.id) == UnitLecturerLink.unit_id,
                    )
                    .join(
                        Lecturer,
                        onclause=or_(
                            col(UnitExaminerLink.lecturer_id) == Lecturer.id,
                            col(UnitLecturerLink.lecturer_id) == Lecturer.id,
                        ),
                    )
                )

            query = join_lecturer(query)
            final_query = join_lecturer(final_query)

        if any(f.key == "offered" for f in filters):

            def join_section[T: Select[Any, Any, Any] | SelectOfScalar[Any]](
                q: T,
            ) -> T:
                return q.join(
                    UnitSectionLink,
                    onclause=col(LearningUnit.id) == UnitSectionLink.unit_id,
                ).join(
                    SectionPathView,
                    onclause=col(UnitSectionLink.section_id) == SectionPathView.id,
                )

            query = join_section(query)
            final_query = join_section(final_query)

        average_rating = None
        if any(f.key == "coursereview" for f in filters) or order_by == "coursereview":

            def join_rating[T: Select[Any, Any, Any] | SelectOfScalar[Any]](
                q: T,
            ) -> T:
                return q.join(
                    Rating, onclause=col(LearningUnit.number) == Rating.course_number
                )

            query = join_rating(query)
            final_query = join_rating(final_query)

            average_rating = (
                col(Rating.recommended)
                + col(Rating.engaging)
                + col(Rating.difficulty)
                + col(Rating.effort)
                + col(Rating.resources)
            ) / 5

        ###################
        # Build the query #
        ###################
        clause, filters_used = _build_boolean_clause(filters)

        # we consider units with missing numbers a fluke anyway
        query = query.where(clause, col(LearningUnit.number).is_not(None))

        #########
        # Order #
        #########
        order_by_clauses = []
        default_order_clauses = [
            col(LearningUnit.title_english).asc(),
            col(LearningUnit.title).asc(),
            year.desc(),
        ]
        match order_by:
            case "title" | "title_english":
                order_by_clauses = [col(LearningUnit.title_english)]
            case "title_german":
                order_by_clauses = [col(LearningUnit.title)]
            case "number":
                order_by_clauses = [col(LearningUnit.number)]
            case "credits":
                order_by_clauses = [col(LearningUnit.credits)]
            case "semester":
                order_by_clauses = [semester]
            case "lecturer":
                order_by_clauses = [col(Lecturer.surname), col(Lecturer.name)]
            case "department":
                order_by_clauses = [col(LearningUnit.departments)]
            case "level":
                order_by_clauses = [col(LearningUnit.levels)]
            case "language":
                order_by_clauses = [col(LearningUnit.language)]
            case "coursereview":
                if average_rating is not None:
                    order_by_clauses = [average_rating]
            case (
                "year"
                | "descriptions"
                | "descriptions_english"
                | "descriptions_german"
                | "offered"
                | "examtype"
                | "priority"
                | "restricted"
                | "primary_target_group"
            ):
                pass
        if descending:
            query = query.order_by(
                *(x.desc() for x in order_by_clauses),
                *(x for x in default_order_clauses),
            )
        else:
            query = query.order_by(
                *(x.asc() for x in order_by_clauses),
                *(x for x in default_order_clauses),
            )

        # The final_query finds all relevant course numbers of any matched units, so that all units can be grouped by
        # number and be returned. Basically, if a unit is filtered out, but another unit of the same course number is still in the results, we want to return all units of that course number.
        # We filter for all unit numbers that can be shown as results (with sorting + page limits)
        # For example: https://vvzapi.ch/unit/199098 got renamed from "Geo.BigData(Science)" to "Geospatial data processing with AI tools – an overview".
        # Searching for "big data" would match the old one, but the new one would show if we didn't re-apply filters.
        valid_numbers = (
            query.with_only_columns(col(LearningUnit.number))
            .distinct()
            .offset(offset)
            .limit(limit)
        )

        final_query = final_query.where(
            col(LearningUnit.number).in_(valid_numbers)
        ).distinct()

        if descending:
            final_query = final_query.order_by(
                *(x.desc() for x in order_by_clauses),
                *(x for x in default_order_clauses),
            )
        else:
            final_query = final_query.order_by(
                *(x.asc() for x in order_by_clauses),
                *(x for x in default_order_clauses),
            )

        async def _count() -> int:
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("count"),
                    tracer.start_as_current_span("execute_count_query"),
                ):
                    count_query = query.with_only_columns(
                        func.count(distinct(LearningUnit.number))
                    ).order_by(None)
                    count = await session.scalar(count_query) or 0
            return count

        async def _count_ids() -> int:
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("count"),
                    tracer.start_as_current_span("execute_count_query"),
                ):
                    count_query = query.with_only_columns(
                        func.count(distinct(LearningUnit.id))
                    ).order_by(None)
                    count = await session.scalar(count_query) or 0
            return count

        async def _ids_page() -> list[int]:
            # The ids view pages over matching units, not course numbers, so the
            # filter is applied to each unit directly.
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("fetch"),
                    tracer.start_as_current_span("execute_ids_query"),
                ):
                    ids = (
                        (
                            await session.execute(
                                # Uses the `query` with filtered units, NOT the `final_query` with filtered course numbers
                                query.with_only_columns(col(LearningUnit.id))
                                .distinct()
                                .order_by(col(LearningUnit.id))
                                .offset(offset)
                                .limit(limit)
                            )
                        )
                        .scalars()
                        .all()
                    )
            return list(ids)

        async def _numbers_page() -> list[str]:
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("fetch"),
                    tracer.start_as_current_span("execute_numbers_query"),
                ):
                    rows = (await session.execute(valid_numbers)).scalars().all()
            return list(rows)

        async def _full_results() -> tuple[list[LearningUnit], dict[str, float]]:
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("fetch"),
                    tracer.start_as_current_span("execute_final_query"),
                ):
                    results = (await session.exec(final_query)).all()
                numbers = {unit.number for unit in results if unit.number}
                ratings: dict[str, float] = {}
                if numbers:
                    with (
                        observe_stage("ratings"),
                        tracer.start_as_current_span("execute_ratings_query"),
                    ):
                        rating_rows = (
                            await session.exec(
                                select(Rating).where(
                                    col(Rating.course_number).in_(numbers)
                                )
                            )
                        ).all()
                    ratings = {r.course_number: r.average() for r in rating_rows}
                session.expunge_all()
            return list(results), ratings

        async def _compact_units() -> list[LearningUnit]:
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("fetch"),
                    tracer.start_as_current_span("execute_compact_query"),
                ):
                    units = (
                        await session.exec(
                            select(LearningUnit)
                            .options(_compact_load_option())
                            .where(col(LearningUnit.number).in_(valid_numbers))
                        )
                    ).all()
                session.expunge_all()
            return list(units)

        async def _compact_ratings() -> dict[str, float]:
            async with AsyncSession(aengine) as session:
                with (
                    observe_stage("ratings"),
                    tracer.start_as_current_span("execute_ratings_query"),
                ):
                    rating_rows = (
                        await session.exec(
                            select(Rating).where(
                                col(Rating.course_number).in_(valid_numbers)
                            )
                        )
                    ).all()
            return {row.course_number: row.average() for row in rating_rows}

        match result_view:
            case SearchResultView.numbers:
                count, numbers_page = await asyncio.gather(_count(), _numbers_page())
                span.set_attribute("total_count", count)
                span.set_attribute("result_count", len(numbers_page))
                return SearchMatch(
                    count=count, filters_used=filters_used, numbers=numbers_page
                )

            case SearchResultView.ids:
                count, ids = await asyncio.gather(_count_ids(), _ids_page())
                span.set_attribute("total_count", count)
                span.set_attribute("result_count", len(ids))
                return SearchMatch(count=count, filters_used=filters_used, ids=ids)

            case SearchResultView.compact:
                count, numbers_page, units, ratings = await asyncio.gather(
                    _count(), _numbers_page(), _compact_units(), _compact_ratings()
                )
                units_by_number: dict[str, list[LearningUnit]] = defaultdict(list)
                for unit in units:
                    if unit.number:
                        units_by_number[unit.number].append(unit)

                compact_results: list[CompactLearningUnit] = []
                for number in numbers_page:
                    number_units = sorted(
                        units_by_number.get(number, []),
                        key=lambda unit: semkez_to_comparable(unit.semkez),
                        reverse=True,
                    )
                    if not number_units:
                        continue
                    latest = number_units[0]
                    compact_results.append(
                        CompactLearningUnit(
                            number=number,
                            title=latest.title,
                            title_english=latest.title_english,
                            credits=latest.credits,
                            levels=latest.levels,
                            departments=latest.departments,
                            language=latest.language,
                            rating=ratings.get(number),
                            semesters={unit.semkez: unit.id for unit in number_units},
                        )
                    )
                span.set_attribute("total_count", count)
                span.set_attribute("result_count", len(compact_results))
                return SearchMatch(
                    count=count,
                    filters_used=filters_used,
                    compact=compact_results,
                )

            case SearchResultView.full:
                count, (results, ratings) = await asyncio.gather(
                    _count(), _full_results()
                )
                numbered_units: dict[str, list[LearningUnit]] = defaultdict(list)
                for unit in results:
                    if unit.number:
                        numbered_units[unit.number].append(unit)
                span.set_attribute("total_count", count)
                span.set_attribute("result_count", len(numbered_units))
                return SearchMatch(
                    count=count,
                    filters_used=filters_used,
                    full={
                        number: GroupedLearningUnits(
                            number=number,
                            units=units,
                            rating=ratings.get(number),
                        )
                        for number, units in numbered_units.items()
                    },
                )


QUERY_DESCRIPTION = (
    'VVZ search query, e.g. `y:2026 s:fs o:"computer science master"`. Plain text '
    "matches course titles. Syntax: https://vvzapi.ch/guide"
)
ORDER_DESCRIPTION = "Sort direction: `asc` or `desc`."
OFFSET_DESCRIPTION = (
    "Number of matching course numbers to skip. Paging is over course numbers, so a "
    "page can contain more units than `limit`."
)
IDS_OFFSET_DESCRIPTION = "Number of matching learning units to skip."


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search learning units (full records)",
    responses={400: {"description": "Bad Request - Invalid query"}},
)
async def search_units(
    query: Annotated[str, Query(alias="q", description=QUERY_DESCRIPTION)],
    request: Request,
    offset: Annotated[Int64, Query(description=OFFSET_DESCRIPTION)] = 0,
    limit: Annotated[
        Int64, Query(ge=1, le=1000, description="Course numbers per page.")
    ] = 20,
    order_by: Annotated[QueryKey, Query(description="Sort key.")] = "year",
    order: Annotated[str, Query(description=ORDER_DESCRIPTION)] = "desc",
) -> SearchResponse:
    """Full learning-unit records, grouped by course number.

    `results` maps each matching course number to all of its learning units across
    semesters, plus the CourseReview rating.

    Lighter representations: `/search/compact` (one summary per course number),
    `/search/numbers` (course numbers only) and `/search/ids` (learning unit ids only).
    """
    page = (offset // limit) + 1
    return await run_search(
        query,
        offset=offset,
        limit=limit,
        order_by=order_by,
        order=order,
        source="api",
        view="api",
        page=page,
        request=request,
        result_view=SearchResultView.full,
    )


@router.get(
    "/compact",
    response_model=CompactSearchResponse,
    summary="Search course summaries (one per course number)",
    responses={400: {"description": "Bad Request - Invalid query"}},
)
async def search_compact(
    query: Annotated[str, Query(alias="q", description=QUERY_DESCRIPTION)],
    request: Request,
    offset: Annotated[Int64, Query(description=OFFSET_DESCRIPTION)] = 0,
    limit: Annotated[
        Int64, Query(ge=1, le=2000, description="Course numbers per page.")
    ] = 20,
    order_by: Annotated[QueryKey, Query(description="Sort key.")] = "year",
    order: Annotated[str, Query(description=ORDER_DESCRIPTION)] = "desc",
) -> CompactSearchResponse:
    """One summary per matching course number instead of full unit records.

    Each entry carries the most recent unit's title(s), credits, levels, departments,
    language and CourseReview rating, plus a `semesters` map of `semkez` -> learning
    unit id (newest first) for resolving full records via `/api/v1/unit/{unit_id}/get`.
    """
    page = (offset // limit) + 1
    return await run_search(
        query,
        offset=offset,
        limit=limit,
        order_by=order_by,
        order=order,
        source="api",
        view="api",
        page=page,
        request=request,
        result_view=SearchResultView.compact,
    )


@router.get(
    "/numbers",
    response_model=NumbersResponse,
    summary="Search course numbers only",
    responses={
        400: {"description": "Bad Request - Invalid query"},
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "total": 2,
                        "results": ["252-0027-00L", "263-0006-00L"],
                        "parsed_query": "title contains 'machine learning'",
                        "exec_time_ms": 12.3,
                    }
                }
            }
        },
    },
)
async def search_numbers(
    query: Annotated[str, Query(alias="q", description=QUERY_DESCRIPTION)],
    request: Request,
    offset: Annotated[Int64, Query(description=OFFSET_DESCRIPTION)] = 0,
    limit: Annotated[
        Int64, Query(ge=1, le=10_000, description="Course numbers per page.")
    ] = 20,
    order_by: Annotated[QueryKey, Query(description="Sort key.")] = "year",
    order: Annotated[str, Query(description=ORDER_DESCRIPTION)] = "desc",
) -> NumbersResponse:
    """Only the matching course numbers (e.g. `252-0027-00L`), no unit data.

    This view answers the filters with a single cheap query and a small response, so its
    `limit` cap is 10,000 instead of 1,000. `total` still counts all matching course
    numbers, not just the returned page.
    """
    page = (offset // limit) + 1
    return await run_search(
        query,
        offset=offset,
        limit=limit,
        order_by=order_by,
        order=order,
        source="api",
        view="api",
        page=page,
        request=request,
        result_view=SearchResultView.numbers,
    )


@router.get(
    "/ids",
    response_model=IdsResponse,
    summary="Search learning unit ids only",
    responses={
        400: {"description": "Bad Request - Invalid query"},
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "total": 3,
                        "results": [193444, 193445, 194002],
                        "parsed_query": "title contains 'machine learning'",
                        "exec_time_ms": 12.3,
                    }
                }
            }
        },
    },
)
async def search_ids(
    query: Annotated[str, Query(alias="q", description=QUERY_DESCRIPTION)],
    request: Request,
    offset: Annotated[Int64, Query(description=IDS_OFFSET_DESCRIPTION)] = 0,
    limit: Annotated[
        Int64,
        Query(ge=1, le=10_000, description="Learning units per page."),
    ] = 20,
    order_by: Annotated[QueryKey, Query(description="Sort key.")] = "year",
    order: Annotated[str, Query(description=ORDER_DESCRIPTION)] = "desc",
) -> IdsResponse:
    """Only the ids of learning units that match the query.

    The filter is applied per learning unit; unlike the other views, results are not
    grouped or paged by course number. `limit`/`offset` page over units and `total` is
    the number of matching units. Resolve an id with `/api/v1/unit/{unit_id}/get`.
    """
    page = (offset // limit) + 1
    return await run_search(
        query,
        offset=offset,
        limit=limit,
        order_by=order_by,
        order=order,
        source="api",
        view="api",
        page=page,
        request=request,
        result_view=SearchResultView.ids,
    )


def _empty_response(result_view: SearchResultView) -> SearchResponseUnion:
    match result_view:
        case SearchResultView.compact:
            return CompactSearchResponse(
                total=0, results=[], parsed_query="", exec_time_ms=0.0
            )
        case SearchResultView.numbers:
            return NumbersResponse(
                total=0, results=[], parsed_query="", exec_time_ms=0.0
            )
        case SearchResultView.ids:
            return IdsResponse(total=0, results=[], parsed_query="", exec_time_ms=0.0)
        case SearchResultView.full:
            return SearchResponse(
                total=0, results={}, parsed_query="", exec_time_ms=0.0
            )


@overload
async def run_search(
    query: str,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
    source: str = "api",
    view: str = "api",
    page: int = 1,
    request: Request | None = None,
    result_view: Literal[SearchResultView.full] = SearchResultView.full,
) -> SearchResponse: ...


@overload
async def run_search(
    query: str,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
    source: str = "api",
    view: str = "api",
    page: int = 1,
    request: Request | None = None,
    result_view: Literal[SearchResultView.compact],
) -> CompactSearchResponse: ...


@overload
async def run_search(
    query: str,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
    source: str = "api",
    view: str = "api",
    page: int = 1,
    request: Request | None = None,
    result_view: Literal[SearchResultView.numbers],
) -> NumbersResponse: ...


@overload
async def run_search(
    query: str,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
    source: str = "api",
    view: str = "api",
    page: int = 1,
    request: Request | None = None,
    result_view: Literal[SearchResultView.ids],
) -> IdsResponse: ...


async def run_search(
    query: str,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
    source: str = "api",
    view: str = "api",
    page: int = 1,
    request: Request | None = None,
    result_view: SearchResultView = SearchResultView.full,
) -> SearchResponseUnion:
    """Run a search and record analytics for it.

    Single choke point for both the web UI (`/`) and the JSON API (`/search`), so
    every search is measured exactly once with the same definitions (see
    `api.analytics.events`). `result_view` selects how much data is materialized and
    which response model is returned.
    """
    with tracer.start_as_current_span("search_units") as span:
        span.set_attribute("query", query)
        span.set_attribute("offset", offset)
        span.set_attribute("limit", limit)
        span.set_attribute("order_by", order_by)
        span.set_attribute("order", order)
        span.set_attribute("source", source)
        span.set_attribute("result_view", result_view.value)

        if len(query.strip()) == 0:
            # Not a search: index views are counted in the `/` handler, and an
            # empty API query is a no-op.
            return _empty_response(result_view)

        started = default_timer()
        count = 0
        matched: SearchMatch | None = None
        filters_used: AND | OR | None = None
        exec_time_ms = 0.0

        with collect_stages() as stages_ms:
            with observe_stage("parse"):
                try:
                    search_operators = build_search_operators(query)
                except ParseException as e:
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"Error parsing query: {e!s}",
                    )

            # default to desc
            descending = not order.startswith("asc")

            start = default_timer()
            try:
                matched = await match_filters(
                    search_operators,
                    offset=offset,
                    limit=limit,
                    order_by=order_by,
                    descending=descending,
                    result_view=result_view,
                )
                count = matched.count
                filters_used = matched.filters_used
            except ValueError:
                span.set_attribute("error", "ValueError in query")
            end = default_timer()
            exec_time_ms = (end - start) * 1000

        duration_seconds = default_timer() - started

        if filters_used is None:
            parsed_query = "ERROR IN QUERY"
            filters: list[tuple[str, str, int]] = []
            boolean_op = "none"
        else:
            parsed_query = str(filters_used)
            if parsed_query.startswith("(") and parsed_query.endswith(")"):
                parsed_query = parsed_query[1:-1]
            filters = query_filters(filters_used)
            boolean_op = boolean_shape(filters_used, len(filters))

        filter_keys = {key for key, _, _ in filters}
        query_type = categorize_query(query, filter_keys)
        client_type = classify_client_for_request(request)

        span.set_attribute("exec_time_ms", exec_time_ms)
        span.set_attribute("total_results", count)
        span.set_attribute("query_type", query_type)
        span.set_attribute("boolean_op", boolean_op)

        SEARCH_REQUESTS.labels(
            source=source,
            client_type=client_type,
            query_type=query_type,
        ).inc()
        SEARCH_RESULT_COUNT.labels(source=source).observe(count)
        if count == 0:
            SEARCH_ZERO_RESULTS.labels(source=source).inc()
        SEARCH_DURATION.labels(
            source=source,
            order_by=order_by,
            order=order,
            view=view,
        ).observe(duration_seconds)
        for filter_key in filter_keys:
            SEARCH_FILTER_USED.labels(filter_key=filter_key).inc()

        record_search(
            request,
            source=source,
            raw_query=query,
            parsed_query=parsed_query,
            filters=filters,
            boolean_op=boolean_op,
            query_type=query_type,
            result_count=count,
            exec_time_ms=exec_time_ms,
            duration_ms=duration_seconds * 1000,
            stages_ms=stages_ms,
            page=page,
            limit=limit,
            order_by=order_by,
            order=order,
            view=view,
        )

        match result_view:
            case SearchResultView.compact:
                return CompactSearchResponse(
                    total=count,
                    results=matched.compact if matched and matched.compact else [],
                    parsed_query=parsed_query,
                    exec_time_ms=exec_time_ms,
                )
            case SearchResultView.numbers:
                return NumbersResponse(
                    total=count,
                    results=matched.numbers if matched and matched.numbers else [],
                    parsed_query=parsed_query,
                    exec_time_ms=exec_time_ms,
                )
            case SearchResultView.ids:
                return IdsResponse(
                    total=count,
                    results=matched.ids if matched and matched.ids else [],
                    parsed_query=parsed_query,
                    exec_time_ms=exec_time_ms,
                )
            case SearchResultView.full:
                return SearchResponse(
                    total=count,
                    results=matched.full if matched and matched.full else {},
                    parsed_query=parsed_query,
                    exec_time_ms=exec_time_ms,
                )

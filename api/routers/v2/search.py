import asyncio
from collections import defaultdict
from timeit import default_timer
from typing import Annotated, cast, override

from fastapi import APIRouter, Query
from opentelemetry import trace
from pydantic import BaseModel
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

from api.models import (
    Department,
    LearningUnit,
    Lecturer,
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

router = APIRouter(prefix="/search", tags=["Search"])

tracer = trace.get_tracer(__name__)


class GroupedLearningUnits(BaseModel):
    number: str
    units: list[LearningUnit]

    @property
    def semkezs(self) -> list[str]:
        return sorted({unit.semkez for unit in self.units if unit.semkez})

    def latest_unit(self) -> LearningUnit | None:
        if not self.units:
            return None
        return max(
            self.units, key=lambda unit: unit.semkez.replace("W", "0").replace("S", "1")
        )

    def with_semkez(self, semkez: str) -> LearningUnit | None:
        for unit in self.units:
            if unit.semkez == semkez:
                return unit
        return None

    @override
    def __iter__(self):
        for unit in sorted(
            self.units,
            key=lambda u: u.semkez.replace("W", "0").replace("S", "1"),
            reverse=True,
        ):
            yield unit.semkez, unit


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
) -> tuple[int, dict[str, GroupedLearningUnits], AND | OR]:
    with tracer.start_as_current_span("match_filters") as span:
        span.set_attribute("offset", offset)
        span.set_attribute("limit", limit)
        span.set_attribute("order_by", order_by)
        span.set_attribute("descending", descending)

        query = select(
            LearningUnit,
            year := sql_cast(func.substr(LearningUnit.semkez, 1, 4), Integer),
            semester := sql_cast(func.substr(LearningUnit.semkez, 5, 1), String),
        )

        #########
        # Joins #
        #########
        if any(f.key == "lecturer" for f in filters) or order_by == "lecturer":
            query = (
                query.join(
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

        if any(f.key == "offered" for f in filters):
            query = query.join(
                UnitSectionLink,
                onclause=col(LearningUnit.id) == UnitSectionLink.unit_id,
            ).join(
                SectionPathView,
                onclause=col(UnitSectionLink.section_id) == SectionPathView.id,
            )

        average_rating = None
        if any(f.key == "coursereview" for f in filters):
            query = query.join(
                Rating, onclause=col(LearningUnit.number) == Rating.course_number
            )
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

        # We filter for all unit numbers that can be shown as results (with sorting + page limits)
        # For example: https://vvzapi.ch/unit/199098 got renamed from "Geo.BigData(Science)" to "Geospatial data processing with AI tools – an overview".
        # Searching for "big data" would match the old one, but the new one would show if we didn't re-apply filters.
        valid_numbers = (
            query.with_only_columns(col(LearningUnit.number))
            .distinct()
            .offset(offset)
            .limit(limit)
        )

        final_query = (
            select(LearningUnit)
            .where(col(LearningUnit.number).in_(valid_numbers))
            .distinct()
        )

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

        async def _count():
            async with AsyncSession(aengine) as session:
                with tracer.start_as_current_span("execute_count_query"):
                    count_query = query.with_only_columns(
                        func.count(distinct(LearningUnit.number))
                    ).order_by(None)
                    (count,) = (await session.execute(count_query)).one()  # pyright: ignore[reportAny]
                    count = cast(int, count)
            return count

        async def _results():
            async with AsyncSession(aengine) as session:
                with tracer.start_as_current_span("execute_final_query"):
                    results = (await session.exec(final_query)).all()
                session.expunge_all()
            return results

        count, results = await asyncio.gather(_count(), _results())

        numbered_units: dict[str, list[LearningUnit]] = defaultdict(list)
        for unit in results:
            if unit.number:
                numbered_units[unit.number].append(unit)

        span.set_attribute("total_count", count)
        span.set_attribute("result_count", len(numbered_units))

        return (
            count,
            {
                number: GroupedLearningUnits(number=number, units=units)
                for number, units in numbered_units.items()
            },
            filters_used,
        )


class SearchResponse(BaseModel):
    total: int
    results: dict[str, GroupedLearningUnits]
    parsed_query: str
    exec_time_ms: float

    @override
    def __iter__(self):
        for unit_number, grouped_units in self.results.items():
            yield unit_number, grouped_units


@router.get("", response_model=SearchResponse)
async def search_units(
    query: Annotated[str, Query(alias="q")],
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
) -> SearchResponse:
    with tracer.start_as_current_span("search_units") as span:
        span.set_attribute("query", query)
        span.set_attribute("offset", offset)
        span.set_attribute("limit", limit)
        span.set_attribute("order_by", order_by)
        span.set_attribute("order", order)

        search_operators = build_search_operators(query)

        # default to desc
        descending = not order.startswith("asc")

        try:
            start = default_timer()
            count, results, filters_used = await match_filters(
                search_operators,
                offset=offset,
                limit=limit,
                order_by=order_by,
                descending=descending,
            )
            end = default_timer()
        except ValueError:
            span.set_attribute("error", "ValueError in query")
            return SearchResponse(
                total=0,
                results={},
                parsed_query="ERROR IN QUERY",
                exec_time_ms=0.0,
            )

        parsed_query = str(filters_used)
        if parsed_query.startswith("(") and parsed_query.endswith(")"):
            parsed_query = parsed_query[1:-1]

        exec_time_ms = (end - start) * 1000
        span.set_attribute("exec_time_ms", exec_time_ms)
        span.set_attribute("total_results", count)

        return SearchResponse(
            total=count,
            results=results,
            parsed_query=parsed_query,
            exec_time_ms=exec_time_ms,
        )

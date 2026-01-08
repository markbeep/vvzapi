from collections import defaultdict
from timeit import default_timer
from typing import Annotated, override

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import exists, literal_column, not_
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement
from sqlmodel import (
    Integer,
    Session,
    String,
    and_,
    col,
    distinct,
    func,
    or_,
    select,
)
from sqlmodel import (
    cast as sql_cast,
)

from api.models import (
    Department,
    LearningUnit,
    Lecturer,
    Section,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
)
from api.util.db import get_session
from api.util.parse_query import (
    AND,
    OR,
    FilterOperator,
    Operator,
    QueryKey,
    build_search_operators,
)
from api.util.sections import concatenate_section_names

router = APIRouter(prefix="/search", tags=["Search"])


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


SectionCTE = concatenate_section_names()


def _build_boolean_clause(op: AND | OR):
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
                clause = col(LearningUnit.title).ilike(f"%{filter_.value}%")
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)
            case "title_english":
                clause = col(LearningUnit.title_english).ilike(f"%{filter_.value}%")
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)
            case "title":
                clause = or_(
                    func.coalesce(LearningUnit.title, "").ilike(f"%{filter_.value}%"),
                    func.coalesce(LearningUnit.title_english, "").ilike(
                        f"%{filter_.value}%"
                    ),
                )
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)
            case "number":
                clause = col(LearningUnit.number).ilike(f"%{filter_.value}%")
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
                            func.substr(LearningUnit.semkez, 1, 4) == str(year_value)
                        )
                    case Operator.ne:
                        booleans.append(
                            func.substr(LearningUnit.semkez, 1, 4) != str(year_value)
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
                            func.substr(LearningUnit.semkez, 1, 4) >= str(year_value)
                        )
                    case Operator.le:
                        booleans.append(
                            func.substr(LearningUnit.semkez, 1, 4) <= str(year_value)
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
                    func.concat(Lecturer.name, " ", Lecturer.surname).ilike(
                        f"%{filter_.value}%"
                    ),
                    func.concat(Lecturer.surname, " ", Lecturer.name).ilike(
                        f"%{filter_.value}%"
                    ),
                )
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)
            case "descriptions_german":
                search_term = f"%{filter_.value}%"
                clause = or_(
                    (func.coalesce(LearningUnit.content, "").ilike(search_term)),
                    (func.coalesce(LearningUnit.literature, "").ilike(search_term)),
                    (func.coalesce(LearningUnit.objective, "").ilike(search_term)),
                    (func.coalesce(LearningUnit.lecture_notes, "").ilike(search_term)),
                    (func.coalesce(LearningUnit.additional, "").ilike(search_term)),
                    (func.coalesce(LearningUnit.comment, "").ilike(search_term)),
                    (func.coalesce(LearningUnit.abstract, "").ilike(search_term)),
                )
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)
            case "descriptions_english":
                search_term = f"%{filter_.value}%"
                clause = or_(
                    (
                        func.coalesce(LearningUnit.content_english, "").ilike(
                            search_term
                        )
                    ),
                    (
                        func.coalesce(LearningUnit.literature_english, "").ilike(
                            search_term
                        )
                    ),
                    (
                        func.coalesce(LearningUnit.objective_english, "").ilike(
                            search_term
                        )
                    ),
                    (
                        func.coalesce(LearningUnit.lecture_notes_english, "").ilike(
                            search_term
                        )
                    ),
                    (
                        func.coalesce(LearningUnit.additional_english, "").ilike(
                            search_term
                        )
                    ),
                    (
                        func.coalesce(LearningUnit.comment_english, "").ilike(
                            search_term
                        )
                    ),
                    (
                        func.coalesce(LearningUnit.abstract_english, "").ilike(
                            search_term
                        )
                    ),
                )
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)
            case "descriptions":
                search_term = f"%{filter_.value}%"
                clause = or_(
                    (func.coalesce(LearningUnit.content, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.content_english, "").ilike(
                            search_term
                        )
                    ),
                    (func.coalesce(LearningUnit.literature, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.literature_english, "").ilike(
                            search_term
                        )
                    ),
                    (func.coalesce(LearningUnit.objective, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.objective_english, "").ilike(
                            search_term
                        )
                    ),
                    (func.coalesce(LearningUnit.lecture_notes, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.lecture_notes_english, "").ilike(
                            search_term
                        )
                    ),
                    (func.coalesce(LearningUnit.additional, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.additional_english, "").ilike(
                            search_term
                        )
                    ),
                    (func.coalesce(LearningUnit.comment, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.comment_english, "").ilike(
                            search_term
                        )
                    ),
                    (func.coalesce(LearningUnit.abstract, "").ilike(search_term)),
                    (
                        func.coalesce(LearningUnit.abstract_english, "").ilike(
                            search_term
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
                clause = exists(
                    (
                        select(1)
                        .select_from(func.json_each(LearningUnit.departments))
                        .where(literal_column("value") == closest_dept.value)
                    )
                )
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
                clause = col(LearningUnit.levels).icontains(filter_.value)
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
                clause = col(LearningUnit.language).icontains(filter_.value)
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
                clause = col(LearningUnit.exam_type).icontains(filter_.value)
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                booleans.append(clause)
                filters_used.ops.append(filter_)

    # matches all filters
    if offered_in_names:
        clauses = (
            SectionCTE.c.path_en.icontains(name) | SectionCTE.c.path_de.icontains(name)
            for name in offered_in_names
        )
        if isinstance(op, OR):
            clauses = or_(*clauses)
        else:
            clauses = and_(*clauses)
        offered_ids = SectionCTE.where(clauses).with_only_columns(SectionCTE.c.id)
        booleans.append(col(Section.id).in_(offered_ids))
    if not_offered_in_names:
        clauses = (
            SectionCTE.c.path_en.icontains(name) | SectionCTE.c.path_de.icontains(name)
            for name in not_offered_in_names
        )
        if isinstance(op, OR):
            clauses = or_(*clauses)
        else:
            clauses = and_(*clauses)
        not_offered_ids = SectionCTE.where(clauses).with_only_columns(SectionCTE.c.id)
        booleans.append(not_(col(Section.id).in_(not_offered_ids)))

    if isinstance(op, AND):
        return and_(*booleans), filters_used
    else:
        return or_(*booleans), filters_used


def match_filters(
    session: Session,
    filters: AND | OR,
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    descending: bool = True,
) -> tuple[int, dict[str, GroupedLearningUnits], AND | OR]:
    query = select(
        LearningUnit,
        year := sql_cast(func.substr(LearningUnit.semkez, 1, 4), Integer),
        semester := sql_cast(func.substr(LearningUnit.semkez, 5, 1), String),
    )
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
            UnitSectionLink, onclause=col(LearningUnit.id) == UnitSectionLink.unit_id
        ).join(Section, onclause=col(UnitSectionLink.section_id) == Section.id)

    clause, filters_used = _build_boolean_clause(filters)

    # we consider units with missing numbers a fluke anyway
    query = query.where(clause, col(LearningUnit.number).is_not(None))

    # total unique numbered units with the filters
    subquery = query.subquery()
    count = session.exec(
        select(func.count(distinct(subquery.c.number))).select_from(subquery)
    ).one()

    # ordering
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

    # We first filter by numbers that are shown on the page (with sorting + page limits)
    # for the results we also apply all filters again, since it is possible for a number to match,
    # but all the information having been changed.
    # For example: https://vvzapi.ch/unit/199098 got renamed from "Geo.BigData(Science)" to "Geospatial data processing with AI tools – an overview".
    # Searching for "big data" would match the old one, but the new one would show if we didn't re-apply filters.
    valid_numbers = (
        query.with_only_columns(col(LearningUnit.number))
        .distinct()
        .offset(offset)
        .limit(limit)
    )
    results = session.exec(
        query.where(col(LearningUnit.number).in_(valid_numbers))
    ).all()

    numbered_units: dict[str, list[LearningUnit]] = defaultdict(list)
    for unit, _, _ in results:
        if unit.number:
            numbered_units[unit.number].append(unit)

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


@router.get("/", response_model=SearchResponse)
async def search_units(
    query: Annotated[str, Query(alias="q")],
    session: Annotated[Session, Depends(get_session)],
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    order: str = "desc",
) -> SearchResponse:
    search_operators = build_search_operators(query)

    # default to desc
    descending = not order.startswith("asc")

    start = default_timer()
    count, results, filters_used = match_filters(
        session,
        search_operators,
        offset=offset,
        limit=limit,
        order_by=order_by,
        descending=descending,
    )
    end = default_timer()

    parsed_query = str(filters_used)
    if parsed_query.startswith("(") and parsed_query.endswith(")"):
        parsed_query = parsed_query[1:-1]

    return SearchResponse(
        total=count,
        results=results,
        parsed_query=parsed_query,
        exec_time_ms=(end - start) * 1000,
    )

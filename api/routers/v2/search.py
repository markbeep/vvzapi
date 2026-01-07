from typing import override
import re
from collections import defaultdict
from enum import Enum
from typing import Annotated, Literal, cast, get_args

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from rapidfuzz import fuzz, process, utils
from sqlalchemy import exists, literal_column, not_
from sqlmodel import (
    Integer,
    Session,
    String,
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
from api.util.sections import concatenate_section_names

router = APIRouter(prefix="/search", tags=["Search"])

# Matches query operators ('c:analysis y>=2020')
query_ops = re.compile(
    r'(\w+)(:|=|>|<|(?:<=)|(?:>=)|(?:!:))(\w+|(?:".+?")|(?:\'.+?\'))'
)


# TODO: add more keys
QueryKey = Literal[
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
]

mapping: dict[str, QueryKey] = {
    "t": "title",
    "n": "number",
    "c": "credits",
    "mv": "credits",
    "ects": "credits",
    "tg": "title_german",
    "te": "title_english",
    "y": "year",
    "s": "semester",
    "l": "lecturer",
    "i": "lecturer",
    "instructor": "lecturer",
    "d": "descriptions",
    "dg": "descriptions_german",
    "de": "descriptions_english",
    "dep": "department",
    "lvl": "level",
    "lev": "level",
    "lang": "language",
    "offeredin": "offered",
    "o": "offered",
    "off": "offered",
    "e": "examtype",
}


class Operator(str, Enum):
    eq = "="
    ne = "!="
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="

    def __str__(self) -> str:
        return self.value


class FilterOperatorUnparsed(BaseModel):
    key: QueryKey
    operator: str
    value: str


class FilterOperator(BaseModel):
    key: QueryKey
    operator: Operator
    value: str

    def __str__(self) -> str:
        return f"{self.key} {self.operator} {self.value}"


def find_closest_operators(key: str) -> QueryKey | None:
    """Best effort to try to figure out what key a user meant"""
    key = key.lower()
    if key in mapping:
        return mapping[key]
    if key in get_args(QueryKey):
        return cast(QueryKey, key)

    # first see if there's a key that starts the same
    for query_key in get_args(QueryKey):
        if query_key.startswith(key):
            return query_key

    # try to figure out the closest match
    if result := process.extractOne(
        key,
        get_args(QueryKey),
        scorer=fuzz.partial_ratio,
        processor=utils.default_process,
    ):
        matched_name, score, _ = result
        if score >= 60:
            return cast(QueryKey, matched_name)
    return None


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

    def __iter__(self):
        for unit in sorted(
            self.units,
            key=lambda u: u.semkez.replace("W", "0").replace("S", "1"),
            reverse=True,
        ):
            yield unit.semkez, unit


def match_filters(
    session: Session,
    filters: list[FilterOperator],
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    descending: bool = True,
) -> tuple[int, dict[str, GroupedLearningUnits], list[FilterOperator]]:
    filters_used: list[FilterOperator] = []

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

    offered_in_names: set[str] = set()
    not_offered_in_names: set[str] = set()
    if any(f.key == "offered" for f in filters):
        query = query.join(
            UnitSectionLink, onclause=col(LearningUnit.id) == UnitSectionLink.unit_id
        ).join(Section, onclause=col(UnitSectionLink.section_id) == Section.id)

    for filter_ in filters:
        match filter_.key:
            case "title_german":
                clause = col(LearningUnit.title).ilike(f"%{filter_.value}%")
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                query = query.where(clause)
                filters_used.append(filter_)
            case "title_english":
                clause = col(LearningUnit.title_english).ilike(f"%{filter_.value}%")
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                query = query.where(clause)
                filters_used.append(filter_)
            case "title":
                clause = or_(
                    func.coalesce(LearningUnit.title, "").ilike(f"%{filter_.value}%"),
                    func.coalesce(LearningUnit.title_english, "").ilike(
                        f"%{filter_.value}%"
                    ),
                )
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                query = query.where(clause)
                filters_used.append(filter_)
            case "number":
                query = query.where(
                    col(LearningUnit.number).ilike(f"%{filter_.value}%")
                )
                filters_used.append(filter_)
            case "credits":
                try:
                    ects_value = float(filter_.value)
                except ValueError:
                    continue
                match filter_.operator:
                    case Operator.eq:
                        query = query.where(LearningUnit.credits == ects_value)
                    case Operator.ne:
                        query = query.where(LearningUnit.credits != ects_value)
                    case Operator.gt:
                        query = query.where(col(LearningUnit.credits) > ects_value)
                    case Operator.lt:
                        query = query.where(col(LearningUnit.credits) < ects_value)
                    case Operator.ge:
                        query = query.where(col(LearningUnit.credits) >= ects_value)
                    case Operator.le:
                        query = query.where(col(LearningUnit.credits) <= ects_value)
                filters_used.append(filter_)
            case "year":
                if not filter_.value.isdigit():
                    continue
                year_value = int(filter_.value)
                match filter_.operator:
                    case Operator.eq:
                        query = query.where(year == year_value)
                    case Operator.ne:
                        query = query.where(year != year_value)
                    case Operator.gt:
                        query = query.where(year > year_value)
                    case Operator.lt:
                        query = query.where(year < year_value)
                    case Operator.ge:
                        query = query.where(year >= year_value)
                    case Operator.le:
                        query = query.where(year <= year_value)
                filters_used.append(filter_)
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
                    query = query.where(semester != sem_filter)
                else:
                    query = query.where(semester == sem_filter)
                filters_used.append(
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
                query = query.where(clause)
                filters_used.append(filter_)
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
                query = query.where(clause)
                filters_used.append(filter_)
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
                query = query.where(clause)
                filters_used.append(filter_)
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
                query = query.where(clause)
                filters_used.append(filter_)
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
                query = query.where(clause)
                filters_used.append(
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
                query = query.where(clause)
                filters_used.append(
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
                query = query.where(clause)
                filters_used.append(filter_)
            case "offered":
                if filter_.operator == Operator.ne:
                    not_offered_in_names.add(filter_.value)
                else:
                    offered_in_names.add(filter_.value)
                filters_used.append(filter_)
            case "examtype":
                clause = col(LearningUnit.exam_type).icontains(filter_.value)
                if filter_.operator == Operator.ne:
                    clause = not_(clause)
                query = query.where(clause)
                filters_used.append(filter_)

    # matches all filters
    if offered_in_names:
        c = concatenate_section_names()
        offered_in_ids = c.where(
            *(
                c.c.path_en.icontains(name) | c.c.path_de.icontains(name)
                for name in offered_in_names
            )
        ).with_only_columns(c.c.id)
        query = query.where(col(Section.id).in_(offered_in_ids))
    if not_offered_in_names:
        c = concatenate_section_names("not_offered_in_sections")
        not_offered_in_ids = c.where(
            or_(
                *(
                    c.c.path_en.icontains(name) | c.c.path_de.icontains(name)
                    for name in not_offered_in_names
                )
            )
        ).with_only_columns(c.c.id)
        query = query.where(col(Section.id).not_in(not_offered_in_ids))

    # we consider units with missing numbers a fluke anyway
    query = query.where(col(LearningUnit.number).is_not(None))

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
    filters_used: list[FilterOperator]

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
    operators: list[tuple[str, str, str]] = query_ops.findall(query)
    unparsed_filters: list[FilterOperatorUnparsed] = []
    for key, operator, value in operators:
        query = query.replace(f"{key}{operator}{value}", "").strip()
        value = value.strip("\"'")
        if query_key := find_closest_operators(key):
            unparsed_filters.append(
                FilterOperatorUnparsed(
                    key=query_key,
                    operator=operator,
                    value=value,
                )
            )

    # any values without operators are used as title filters
    query = re.sub(r"\s+", " ", query).strip()
    if query:
        for word in query.split(" "):
            unparsed_filters.append(
                FilterOperatorUnparsed(
                    key="title",
                    operator="=",
                    value=word,
                )
            )

    # convert to FilterOperator (basically just turn colons into equals)
    filters: list[FilterOperator] = []
    for filter_ in unparsed_filters:
        if filter_.operator == ":":
            operator = Operator.eq
        elif filter_.operator == "!:":
            operator = Operator.ne
        else:
            try:
                operator = Operator(filter_.operator)
            except ValueError:
                continue
        filters.append(
            FilterOperator(
                key=filter_.key,
                operator=operator,
                value=filter_.value,
            )
        )

    # default to desc
    descending = not order.startswith("asc")

    count, results, filters_used = match_filters(
        session,
        filters,
        offset=offset,
        limit=limit,
        order_by=order_by,
        descending=descending,
    )

    return SearchResponse(total=count, results=results, filters_used=filters_used)

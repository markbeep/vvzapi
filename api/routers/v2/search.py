from enum import Enum
from typing import Annotated, Literal, Sequence, cast
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case
from sqlmodel import (
    Integer,
    String,
    Session,
    col,
    not_,
    or_,
    select,
    cast as sql_cast,
    func,
)
import re
from rapidfuzz import fuzz

from api.models import (
    Department,
    LearningUnit,
    Lecturer,
    UnitExaminerLink,
    UnitLecturerLink,
)
from api.util.db import get_session


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
}


class Operator(str, Enum):
    eq = "="
    ne = "!="
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="


class FilterOperatorUnparsed(BaseModel):
    key: QueryKey
    operator: str
    value: str


class FilterOperator(BaseModel):
    key: QueryKey
    operator: Operator
    value: str


def find_closest_operators(key: str) -> QueryKey | None:
    """Best effort to try to figure out what key a user meant"""
    key = key.lower()
    if key in mapping:
        return mapping[key]
    if key in QueryKey.__args__:
        return cast(QueryKey, key)

    # first see if there's a key that starts the same
    for query_key in QueryKey.__args__:
        if query_key.startswith(key):
            return query_key

    # try to figure out the closest match
    top: Sequence[tuple[QueryKey, float]] = sorted(
        [
            (query_key, fuzz.partial_ratio(key, query_key))
            for query_key in QueryKey.__args__
        ],
        reverse=True,
    )
    if len(top) > 0:
        return top[0][0]

    return None


def _get_acronym(department: Department) -> str:
    name = str(department.name).replace("_", " ")
    # TODO: find proper acronyms like "ITET" for "Information Technology and Electrical Engineering"
    acronym = "".join(word[0].upper() for word in name.split(" ") if word)
    return name + f" ({acronym})"


def match_filters(
    session: Session,
    filters: list[FilterOperator],
    *,
    offset: int = 0,
    limit: int = 20,
    order_by: QueryKey = "year",
    descending: bool = True,
) -> tuple[int, list[LearningUnit]]:
    department_map = {dept.name: _get_acronym(dept) for dept in Department}
    query = select(
        LearningUnit,
        year := sql_cast(func.substr(LearningUnit.semkez, 1, 4), Integer),
        semester := sql_cast(func.substr(LearningUnit.semkez, 5, 1), String),
        department := case(department_map, value=LearningUnit.department, else_=""),
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

    for filter_ in filters:
        if filter_.key == "title_german":
            clause = col(LearningUnit.title).ilike(f"%{filter_.value}%")
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)
        elif filter_.key == "title_english":
            clause = col(LearningUnit.title_english).ilike(f"%{filter_.value}%")
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)
        elif filter_.key == "title":
            clause = or_(
                func.coalesce(LearningUnit.title, "").ilike(f"%{filter_.value}%"),
                func.coalesce(LearningUnit.title_english, "").ilike(
                    f"%{filter_.value}%"
                ),
            )
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)
        elif filter_.key == "number":
            query = query.where(col(LearningUnit.number).ilike(f"%{filter_.value}%"))
        elif filter_.key == "credits":
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
        elif filter_.key == "year":
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
        elif filter_.key == "semester":
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
        elif filter_.key in ["lecturer", "i", "instructor"]:
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
        elif filter_.key == "descriptions_german":
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
        elif filter_.key == "descriptions_english":
            search_term = f"%{filter_.value}%"
            clause = or_(
                (func.coalesce(LearningUnit.content_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.literature_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.objective_english, "").ilike(search_term)),
                (
                    func.coalesce(LearningUnit.lecture_notes_english, "").ilike(
                        search_term
                    )
                ),
                (func.coalesce(LearningUnit.additional_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.comment_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.abstract_english, "").ilike(search_term)),
            )
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)
        elif filter_.key == "descriptions":
            search_term = f"%{filter_.value}%"
            clause = or_(
                (func.coalesce(LearningUnit.content, "").ilike(search_term)),
                (func.coalesce(LearningUnit.content_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.literature, "").ilike(search_term)),
                (func.coalesce(LearningUnit.literature_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.objective, "").ilike(search_term)),
                (func.coalesce(LearningUnit.objective_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.lecture_notes, "").ilike(search_term)),
                (
                    func.coalesce(LearningUnit.lecture_notes_english, "").ilike(
                        search_term
                    )
                ),
                (func.coalesce(LearningUnit.additional, "").ilike(search_term)),
                (func.coalesce(LearningUnit.additional_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.comment, "").ilike(search_term)),
                (func.coalesce(LearningUnit.comment_english, "").ilike(search_term)),
                (func.coalesce(LearningUnit.abstract, "").ilike(search_term)),
                (func.coalesce(LearningUnit.abstract_english, "").ilike(search_term)),
            )
            if filter_.operator == Operator.ne:
                clause = not_(clause)
                print("negating descriptions", clause)
            query = query.where(clause)
        elif filter_.key == "department":
            clause = department.ilike(f"%{filter_.value}%")
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)
        elif filter_.key == "level":
            clause = col(LearningUnit.levels).ilike(f"%{filter_.value}%")
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)
        elif filter_.key == "language":
            clause = col(LearningUnit.language).ilike(f"%{filter_.value}%")
            if filter_.operator == Operator.ne:
                clause = not_(clause)
            query = query.where(clause)

    # count is in separate query to make it easier
    count = session.exec(select(func.count()).select_from(query.subquery())).one()

    # ordering
    order_by_clauses = [year]
    default_order_clauses = [col(LearningUnit.title_english), col(LearningUnit.title)]
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
        case "year" | "descriptions" | "descriptions_english" | "descriptions_german":
            pass
        case "department":
            order_by_clauses = [department]
        case "level":
            order_by_clauses = [col(LearningUnit.levels)]
        case "language":
            order_by_clauses = [col(LearningUnit.language)]
    if descending:
        query = query.order_by(
            *(x.desc() for x in order_by_clauses),
            *(x.asc() for x in default_order_clauses),
        )
    else:
        query = query.order_by(
            *(x.asc() for x in order_by_clauses),
            *(x.asc() for x in default_order_clauses),
        )

    results = session.exec(query.offset(offset).limit(limit)).all()

    return count, [unit for unit, _, _, _ in results]


class SearchResponse(BaseModel):
    total: int
    results: list[LearningUnit]


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
        unparsed_filters.append(
            FilterOperatorUnparsed(
                key="title",
                operator="=",
                value=query,
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

    count, results = match_filters(
        session,
        filters,
        offset=offset,
        limit=limit,
        order_by=order_by,
        descending=descending,
    )
    return SearchResponse(total=count, results=results)

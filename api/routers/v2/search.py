from enum import Enum
from typing import Annotated, Literal, Sequence, cast
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Integer, String, Session, col, or_, select, cast as sql_cast, func
import re
from rapidfuzz import fuzz

from api.models import (
    LearningUnit,
    Lecturer,
    UnitExaminerLink,
    UnitLecturerLink,
)
from api.util.db import get_session


router = APIRouter(prefix="/search", tags=["Search"])

# Matches query operators ('c:analysis y>=2020')
query_ops = re.compile(r'(\w+)(:|=|>|<|(?:<=)|(?:>=))(\w+|(?:".+?")|(?:\'.+?\'))')


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


def match_filters(
    session: Session, filters: list[FilterOperator], *, offset: int = 0, limit: int = 20
) -> tuple[int, list[LearningUnit]]:
    query = select(
        LearningUnit,
        year := sql_cast(func.substr(LearningUnit.semkez, 1, 4), Integer),
        semester := sql_cast(func.substr(LearningUnit.semkez, 5, 1), String),
    )
    if any(f.key == "lecturer" for f in filters):
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
            query = query.where(col(LearningUnit.title).ilike(f"%{filter_.value}%"))
        elif filter_.key == "title_english":
            query = query.where(
                col(LearningUnit.title_english).ilike(f"%{filter_.value}%")
            )
        elif filter_.key == "title":
            query = query.where(
                or_(
                    col(LearningUnit.title).ilike(f"%{filter_.value}%"),
                    col(LearningUnit.title_english).ilike(f"%{filter_.value}%"),
                )
            )
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
            query = query.where(semester == sem_filter)
        elif filter_.key in ["lecturer", "i", "instructor"]:
            query = query.where(
                or_(
                    func.concat(Lecturer.name, " ", Lecturer.surname).ilike(
                        f"%{filter_.value}%"
                    ),
                    func.concat(Lecturer.surname, " ", Lecturer.name).ilike(
                        f"%{filter_.value}%"
                    ),
                )
            )
        elif filter_.key == "descriptions_german":
            search_term = f"%{filter_.value}%"
            query = query.where(
                or_(
                    (col(LearningUnit.content).ilike(search_term)),
                    (col(LearningUnit.literature).ilike(search_term)),
                    (col(LearningUnit.objective).ilike(search_term)),
                    (col(LearningUnit.lecture_notes).ilike(search_term)),
                    (col(LearningUnit.additional).ilike(search_term)),
                    (col(LearningUnit.comment).ilike(search_term)),
                    (col(LearningUnit.abstract).ilike(search_term)),
                )
            )
        elif filter_.key == "descriptions_english":
            search_term = f"%{filter_.value}%"
            query = query.where(
                or_(
                    (col(LearningUnit.content_english).ilike(search_term)),
                    (col(LearningUnit.literature_english).ilike(search_term)),
                    (col(LearningUnit.objective_english).ilike(search_term)),
                    (col(LearningUnit.lecture_notes_english).ilike(search_term)),
                    (col(LearningUnit.additional_english).ilike(search_term)),
                    (col(LearningUnit.comment_english).ilike(search_term)),
                    (col(LearningUnit.abstract_english).ilike(search_term)),
                )
            )
        elif filter_.key == "descriptions":
            search_term = f"%{filter_.value}%"
            query = query.where(
                or_(
                    (col(LearningUnit.content).ilike(search_term)),
                    (col(LearningUnit.content_english).ilike(search_term)),
                    (col(LearningUnit.literature).ilike(search_term)),
                    (col(LearningUnit.literature_english).ilike(search_term)),
                    (col(LearningUnit.objective).ilike(search_term)),
                    (col(LearningUnit.objective_english).ilike(search_term)),
                    (col(LearningUnit.lecture_notes).ilike(search_term)),
                    (col(LearningUnit.lecture_notes_english).ilike(search_term)),
                    (col(LearningUnit.additional).ilike(search_term)),
                    (col(LearningUnit.additional_english).ilike(search_term)),
                    (col(LearningUnit.comment).ilike(search_term)),
                    (col(LearningUnit.comment_english).ilike(search_term)),
                    (col(LearningUnit.abstract).ilike(search_term)),
                    (col(LearningUnit.abstract_english).ilike(search_term)),
                )
            )

    # TODO: add ordering: unclear how to implement this cleanly. Might make sense to just
    # have it as an extra parameter in the request instead of an operator

    count = session.exec(select(func.count()).select_from(query.subquery())).one()
    results = session.exec(query.offset(offset).limit(limit)).all()
    return count, [unit for unit, _, _ in results]


class SearchResponse(BaseModel):
    total: int
    results: list[LearningUnit]


@router.get("/", response_model=SearchResponse)
async def search_units(
    query: Annotated[str, Query(alias="q")],
    session: Annotated[Session, Depends(get_session)],
    offset: int = 0,
    limit: int = 20,
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
    filters = [
        FilterOperator(
            key=filter_.key,
            operator=Operator.eq
            if filter_.operator == ":"
            else Operator(filter_.operator),
            value=filter_.value,
        )
        for filter_ in unparsed_filters
    ]

    count, results = match_filters(session, filters, offset=offset, limit=limit)
    return SearchResponse(total=count, results=results)

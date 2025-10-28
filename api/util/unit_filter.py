from typing import Any, cast
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy import ColumnExpressionArgument
from sqlmodel import Session, and_, col, or_
from sqlmodel.sql._expression_select_cls import Select, SelectOfScalar

from api.models import (
    Department,
    LearningUnit,
    Level,
    Periodicity,
    Section,
    UnitSectionLink,
)
from api.util.sections import get_child_sections


class VVZFilters(BaseModel):
    # base
    semkez: str | None = None
    level: Level | None = None
    department: Department | None = None

    # "Structure"
    section: int | None = None
    """only a single section is required, unlike on VVZ"""

    # "Further criteria"
    number: str | None = None
    title: str | None = None
    lecturer_id: int | None = None
    lecturer_name: str | None = None
    lecturer_surname: str | None = None
    type: str | None = None
    """Unit type: O, W+, W, E-, Z, Dr"""
    language: str | None = None
    periodicity: int | None = None
    """
    - ONETIME = 0
    - ANNUAL = 1
    - SEMESTER = 2
    - BIENNIAL = 3
    """
    ects_min: float | None = None
    ects_max: float | None = None
    content_search: str | None = None
    """Called 'Catalogue data' on VVZ"""

    vvz_sort: bool = False
    """Sort the same way as vvz"""


def get_vvz_filters(request: Request) -> VVZFilters:
    params = request.query_params

    level = params.get("level")
    if level is not None:
        try:
            level = Level(level)
        except ValueError:
            level = None

    department = params.get("department")
    if department is not None:
        try:
            department = Department(int(department))
        except ValueError:
            department = None

    ects_min = params.get("ects_min")
    ects_min = float(ects_min) if ects_min is not None else None
    ects_max = params.get("ects_max")
    ects_max = float(ects_max) if ects_max is not None else None

    filters = VVZFilters(
        semkez=params.get("semkez"),
        level=level,
        department=department,
        section=int(params["section"]) if "section" in params else None,
        number=params.get("number"),
        title=params.get("title"),
        lecturer_id=int(params["lecturer_id"]) if "lecturer_id" in params else None,
        lecturer_name=params.get("lecturer_name"),
        lecturer_surname=params.get("lecturer_surname"),
        type=params.get("type"),
        language=params.get("language"),
        periodicity=int(params["periodicity"]) if "periodicity" in params else None,
        ects_min=ects_min,
        ects_max=ects_max,
        content_search=params.get("content_search"),
        vvz_sort=params.get("vvz_sort", "").lower() in ["true", "1", "yes"],
    )
    return filters


def build_vvz_filter[T: Select[Any] | SelectOfScalar[Any]](
    session: Session, query: T, filters: VVZFilters
) -> T:
    match filters.periodicity:
        case 0:
            periodicity = Periodicity.ONETIME
        case 1:
            periodicity = Periodicity.ANNUAL
        case 2:
            periodicity = Periodicity.SEMESTER
        case 3:
            periodicity = Periodicity.BIENNIAL
        case _:
            periodicity = None

    if filters.section is not None or filters.type is not None or filters.vvz_sort:
        query = query.join(UnitSectionLink)
    if filters.vvz_sort:
        query = query.join(Section).order_by(
            col(Section.name).asc(), col(LearningUnit.title).asc()
        )

    query_filters: list[ColumnExpressionArgument[bool] | bool] = []

    if filters.section is not None:
        child_sections = get_child_sections(session, filters.section)
        section_ids = [x.id for x in child_sections] + [filters.section]
        query_filters.append(col(UnitSectionLink.section_id).in_(section_ids))
    if filters.semkez is not None:
        query_filters.append(LearningUnit.semkez == filters.semkez)
    if filters.level is not None:
        query_filters.append(col(LearningUnit.levels).contains(filters.level))
    if filters.department is not None:
        query_filters.append(LearningUnit.department == filters.department)
    if filters.number is not None:
        query_filters.append(LearningUnit.number == filters.number)
    if filters.title is not None:
        query_filters.append(col(LearningUnit.title).ilike(f"%{filters.title}%"))
    # if filters.lecturer_id is not None:
    #     query_filters.append(
    #         or_(
    #             col(LearningUnit.lecturers).contains(filters.lecturer_id),
    #             col(LearningUnit.examiners).contains(filters.lecturer_id),
    #         )
    #     )
    # TODO: requires lecturers in separate table
    # if filters.lecturer_name is not None:
    #     query = query.where(
    #         LearningUnit.lecturer_name.ilike(f"%{filters.lecturer_name}%")
    #     )
    # if filters.lecturer_surname is not None:
    #     query = query.where(
    #         LearningUnit.lecturer_surname.ilike(f"%{filters.lecturer_surname}%")
    #     )
    if filters.type is not None:
        query_filters.append(UnitSectionLink.type == filters.type)
    if filters.language is not None:
        query_filters.append(col(LearningUnit.language).ilike(f"%{filters.language}%"))
    if periodicity is not None:
        query_filters.append(LearningUnit.course_frequency == periodicity)
    if filters.ects_min is not None:
        query_filters.append(
            and_(
                col(LearningUnit.credits).is_not(None),
                cast(float, LearningUnit.credits) >= filters.ects_min,
            )
        )
    if filters.ects_max is not None:
        query_filters.append(
            and_(
                col(LearningUnit.credits).is_not(None),
                cast(float, LearningUnit.credits) <= filters.ects_max,
            )
        )
    if filters.content_search is not None:
        search_term = f"%{filters.content_search}%"
        query_filters.append(
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

    if query_filters:
        query = query.where(and_(*query_filters))

    return query

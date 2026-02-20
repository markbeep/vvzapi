from typing import Any, cast

from opentelemetry import trace
from pydantic import BaseModel
from sqlalchemy import ColumnExpressionArgument
from sqlmodel import Session, and_, col, or_
from sqlmodel.sql._expression_select_cls import Select, SelectOfScalar

from api.models import (
    Department,
    LearningUnit,
    Lecturer,
    Level,
    Periodicity,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
)
from api.util.sections import get_child_sections

tracer = trace.get_tracer(__name__)


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
    periodicity: Periodicity | None = None
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


def build_vvz_filter[T: Select[Any] | SelectOfScalar[Any]](
    session: Session, query: T, filters: VVZFilters
) -> T:
    with tracer.start_as_current_span("build_vvz_filter") as span:
        if filters.semkez:
            span.set_attribute("semkez", filters.semkez)
        if filters.section:
            span.set_attribute("section", filters.section)
        if filters.number:
            span.set_attribute("number", filters.number)

        if filters.section is not None or filters.type is not None:
            query = query.join(UnitSectionLink)
        if (
            filters.lecturer_id is not None
            or filters.lecturer_name is not None
            or filters.lecturer_surname is not None
        ):
            query = query.join(
                UnitExaminerLink,
                onclause=col(LearningUnit.id) == UnitExaminerLink.unit_id,
            ).join(
                UnitLecturerLink,
                onclause=col(LearningUnit.id) == UnitLecturerLink.unit_id,
            )
        if filters.lecturer_name is not None or filters.lecturer_surname is not None:
            # No need to join lecturers to filter by id only
            query = query.join(
                Lecturer,
                onclause=or_(
                    col(UnitExaminerLink.lecturer_id) == Lecturer.id,
                    col(UnitLecturerLink.lecturer_id) == Lecturer.id,
                ),
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
            query_filters.append(LearningUnit.departments == filters.department)
        if filters.number is not None:
            query_filters.append(LearningUnit.number == filters.number)
        if filters.title is not None:
            query_filters.append(col(LearningUnit.title).like(f"%{filters.title}%"))
        if filters.lecturer_id is not None:
            query_filters.append(
                or_(
                    UnitExaminerLink.lecturer_id == filters.lecturer_id,
                    UnitLecturerLink.lecturer_id == filters.lecturer_id,
                )
            )
        if filters.lecturer_name is not None:
            query_filters.append(
                col(Lecturer.name).like(f"%{filters.lecturer_surname}%")
            )
            query = query.where()
        if filters.lecturer_surname is not None:
            query_filters.append(
                col(Lecturer.surname).like(f"%{filters.lecturer_surname}%")
            )
        if filters.type is not None:
            query_filters.append(UnitSectionLink.type == filters.type)
        if filters.language is not None:
            query_filters.append(
                col(LearningUnit.language).like(f"%{filters.language}%")
            )
        if filters.periodicity is not None:
            query_filters.append(LearningUnit.course_frequency == filters.periodicity)
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
                    (col(LearningUnit.content).like(search_term)),
                    (col(LearningUnit.content_english).like(search_term)),
                    (col(LearningUnit.literature).like(search_term)),
                    (col(LearningUnit.literature_english).like(search_term)),
                    (col(LearningUnit.objective).like(search_term)),
                    (col(LearningUnit.objective_english).like(search_term)),
                    (col(LearningUnit.lecture_notes).like(search_term)),
                    (col(LearningUnit.lecture_notes_english).like(search_term)),
                    (col(LearningUnit.additional).like(search_term)),
                    (col(LearningUnit.additional_english).like(search_term)),
                    (col(LearningUnit.comment).like(search_term)),
                    (col(LearningUnit.comment_english).like(search_term)),
                    (col(LearningUnit.abstract).like(search_term)),
                    (col(LearningUnit.abstract_english).like(search_term)),
                )
            )

        span.set_attribute("filter_count", len(query_filters))

        if query_filters:
            query = query.where(and_(*query_filters))

        return query

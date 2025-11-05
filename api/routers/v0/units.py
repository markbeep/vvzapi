from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from sqlmodel import Session, col, select

from api.env import Settings
from api.models import (
    Department,
    LearningUnit,
    Level,
    Periodicity,
    UnitChanges,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
)
from api.util.db import get_session
from api.util.unit_filter import VVZFilters, build_vvz_filter

router = APIRouter(prefix="/unit", tags=["Learning Units"])


@router.get("/{unit_id}/get", response_model=LearningUnit | None)
@cache(expire=Settings().cache_expiry)
async def get_unit(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> LearningUnit | None:
    return session.get(LearningUnit, unit_id)


@router.get("/{unit_id}/sections", response_model=Sequence[int])
@cache(expire=Settings().cache_expiry)
async def get_unit_sections(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[int]:
    query = (
        select(UnitSectionLink.section_id)
        .where(UnitSectionLink.unit_id == unit_id)
        .offset(offset)
        .limit(limit)
    )
    results = session.exec(query).all()
    return results


@router.get("/{unit_id}/lecturers", response_model=Sequence[int])
@cache(expire=Settings().cache_expiry)
async def get_unit_lecturers(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[int]:
    query = (
        select(UnitLecturerLink.lecturer_id)
        .where(UnitLecturerLink.unit_id == unit_id)
        .offset(offset)
        .limit(limit)
    )
    results = session.exec(query).all()
    return results


@router.get(
    "/{unit_id}/changes",
    response_model=Sequence[UnitChanges],
    description="Get a list of changes that the course details have undergone. "
    "Changes are a JSON object that describe what the values were before they "
    "got updated to either the next change or whatever the model currently has.",
)
@cache(expire=Settings().cache_expiry)
async def get_unit_changes(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[UnitChanges]:
    query = (
        select(UnitChanges)
        .where(UnitChanges.unit_id == unit_id)
        .order_by(col(UnitChanges.scraped_at).desc())
        .offset(offset)
        .limit(limit)
    )
    results = session.exec(query).all()
    return results


@router.get("/{unit_id}/examiners", response_model=Sequence[int])
@cache(expire=Settings().cache_expiry)
async def get_unit_examiners(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[int]:
    query = (
        select(UnitExaminerLink.lecturer_id)
        .where(UnitExaminerLink.unit_id == unit_id)
        .offset(offset)
        .limit(limit)
    )
    results = session.exec(query).all()
    return results


@router.get(
    "/list",
    response_model=Sequence[int],
    description="List learning unit IDs with optional VVZ-like filters",
)
@cache(expire=Settings().cache_expiry)
async def list_units(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    # VVZ filters: base
    semkez: Annotated[
        str | None,
        Query(
            description="Year + semester (Summer/Winter). Format is YYYY[S/W]. Example: 2025S, 2025W."
        ),
    ] = None,
    level: Annotated[Level | None, Query(description="Level of the unit")] = None,
    department: Annotated[
        Department | None,
        Query(
            description="Department offering the unit. 1=ARCHITECTURE, 2=CIVIL_ENVIRONMENTAL_AND_GEOMATIC_ENGINEERING, "
            "3=MECHANICAL_AND_PROCESS_ENGINEERING, 5=COMPUTER_SCIENCE, 7=MANAGEMENT_TECHNOLOGY_AND_ECONOMICS, "
            "8=MATHEMATICS, 9=PHYSICS, 11=BIOLOGY, 13=EARTH_AND_PLANETARY_SCIENCES, 17=HUMANITIES_SOCIAL_AND_POLITICAL_SCIENCES, "
            "18=INFORMATION_TECHNOLOGY_AND_ELECTRICAL_ENGINEERING, 19=MATERIALS, 20=CHEMISTRY_AND_APPLIED_BIOSCIENCES, "
            "23=BIOSYSTEMS_SCIENCE_AND_ENGINEERING, 24=HEALTH_SCIENCES_AND_TECHNOLOGY, 25=ENVIRONMENTAL_SYSTEMS_SCIENCE"
        ),
    ] = None,
    # VVZ filters: "Structure"
    section: Annotated[
        int | None,
        Query(
            description="Section ID to limit results to. Only a single section is required, unlike on VVZ"
        ),
    ] = None,
    # VVZ filters: "Further criteria"
    number: Annotated[str | None, Query(description="Unit number")] = None,
    title: Annotated[
        str | None,
        Query(
            description="Title of the unit. It returns any results where the given title is included in the German or English unit title."
        ),
    ] = None,
    lecturer_id: Annotated[int | None, Query(description="ID of the lecturer")] = None,
    lecturer_name: Annotated[
        str | None, Query(description="Name of the lecturer")
    ] = None,
    lecturer_surname: Annotated[
        str | None, Query(description="Surname of the lecturer")
    ] = None,
    type: Annotated[
        str | None, Query(description="Unit type: O, W+, W, E-, Z, Dr, etc.")
    ] = None,
    language: Annotated[
        str | None, Query(description="Language of instruction")
    ] = None,
    periodicity: Annotated[
        Periodicity | None,
        Query(description="Periodicity:0=ONETIME, 1=ANNUAL, 2=SEMESTER, 3=BIENNIAL"),
    ] = None,
    ects_min: Annotated[float | None, Query(description="Minimum ECTS credits")] = None,
    ects_max: Annotated[float | None, Query(description="Maximum ECTS credits")] = None,
    content_search: Annotated[
        str | None, Query(description="Search within 'Catalogue data' on VVZ")
    ] = None,
) -> Sequence[int]:
    filters = VVZFilters(
        semkez=semkez,
        level=level,
        department=department,
        section=section,
        number=number,
        title=title,
        lecturer_id=lecturer_id,
        lecturer_name=lecturer_name,
        lecturer_surname=lecturer_surname,
        type=type,
        language=language,
        periodicity=periodicity,
        ects_min=ects_min,
        ects_max=ects_max,
        content_search=content_search,
    )
    query = build_vvz_filter(session, select(LearningUnit.id), filters)
    return session.exec(
        query.order_by(col(LearningUnit.id).asc()).offset(offset).limit(limit)
    ).all()

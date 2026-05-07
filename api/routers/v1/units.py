from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from opentelemetry import trace
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from api.models import (
    Department,
    LearningUnit,
    Level,
    Periodicity,
    UnitExaminerLink,
    UnitLecturerLink,
)
from api.util.db import aget_session
from api.util.pydantic_type import Int64, Nullable
from api.util.sections import get_parent_from_unit
from api.util.unit_filter import VVZFilters, build_vvz_filter

tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/unit", tags=["Learning Units"])


@router.get(
    "/{unit_id}/get",
    response_model=LearningUnit | None,
    responses={404: {"description": "Learning unit not found"}},
)
async def get_unit(
    unit_id: Int64,
    session: Annotated[AsyncSession, Depends(aget_session)],
) -> LearningUnit | None:
    with tracer.start_as_current_span("get_unit") as span:
        span.set_attribute("unit_id", unit_id)
        unit = await session.get(LearningUnit, unit_id)
        if not unit:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Learning unit not found"
            )
        return unit


@router.get("/{unit_id}/sections", response_model=Sequence[int])
async def get_unit_sections(
    unit_id: Int64,
    session: Annotated[AsyncSession, Depends(aget_session)],
) -> Sequence[int]:
    with tracer.start_as_current_span("get_unit_sections") as span:
        span.set_attribute("unit_id", unit_id)
        results = (await session.exec(get_parent_from_unit(unit_id))).all()
        span.set_attribute("result_count", len(results))
        return [sec.id for sec in results]


@router.get("/{unit_id}/lecturers", response_model=Sequence[int])
async def get_unit_lecturers(
    unit_id: Int64,
    session: Annotated[AsyncSession, Depends(aget_session)],
    limit: Annotated[Int64, Query(gt=0, le=1000)] = 100,
    offset: Annotated[Int64, Query(ge=0)] = 0,
) -> Sequence[int]:
    with tracer.start_as_current_span("get_unit_lecturers") as span:
        span.set_attribute("unit_id", unit_id)
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)
        query = (
            select(UnitLecturerLink.lecturer_id)
            .where(UnitLecturerLink.unit_id == unit_id)
            .offset(offset)
            .limit(limit)
        )
        results = (await session.exec(query)).all()
        span.set_attribute("result_count", len(results))
        return results


@router.get("/{unit_id}/examiners", response_model=Sequence[int])
async def get_unit_examiners(
    unit_id: Int64,
    session: Annotated[AsyncSession, Depends(aget_session)],
    limit: Annotated[Int64, Query(gt=0, le=1000)] = 100,
    offset: Annotated[Int64, Query(ge=0)] = 0,
) -> Sequence[int]:
    with tracer.start_as_current_span("get_unit_examiners") as span:
        span.set_attribute("unit_id", unit_id)
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)
        query = (
            select(UnitExaminerLink.lecturer_id)
            .where(UnitExaminerLink.unit_id == unit_id)
            .offset(offset)
            .limit(limit)
        )
        results = (await session.exec(query)).all()
        span.set_attribute("result_count", len(results))
        return results


@router.get(
    "/list",
    response_model=Sequence[int],
    description="List learning unit IDs with optional VVZ-like filters",
)
async def list_units(
    session: Annotated[AsyncSession, Depends(aget_session)],
    limit: Annotated[Int64, Query(gt=0, le=1000)] = 100,
    offset: Annotated[Int64, Query(ge=0)] = 0,
    # VVZ filters: base
    semkez: Annotated[
        Nullable[str],
        Query(
            description="Year + semester (Summer/Winter). Format is YYYY[S/W]. Example: 2025S, 2025W."
        ),
    ] = None,
    level: Annotated[Nullable[Level], Query(description="Level of the unit")] = None,
    department: Annotated[
        Nullable[Department],
        Query(
            description="Department offering the unit. 1=ARCHITECTURE, 2=CIVIL_ENVIRONMENTAL_AND_GEOMATIC_ENGINEERING, "
            + "3=MECHANICAL_AND_PROCESS_ENGINEERING, 5=COMPUTER_SCIENCE, 7=MANAGEMENT_TECHNOLOGY_AND_ECONOMICS, "
            + "8=MATHEMATICS, 9=PHYSICS, 11=BIOLOGY, 13=EARTH_AND_PLANETARY_SCIENCES, 17=HUMANITIES_SOCIAL_AND_POLITICAL_SCIENCES, "
            + "18=INFORMATION_TECHNOLOGY_AND_ELECTRICAL_ENGINEERING, 19=MATERIALS, 20=CHEMISTRY_AND_APPLIED_BIOSCIENCES, "
            + "23=BIOSYSTEMS_SCIENCE_AND_ENGINEERING, 24=HEALTH_SCIENCES_AND_TECHNOLOGY, 25=ENVIRONMENTAL_SYSTEMS_SCIENCE"
        ),
    ] = None,
    # VVZ filters: "Structure"
    section: Annotated[
        Nullable[Int64],
        Query(
            description="Section ID to limit results to. Only a single section is required, unlike on VVZ"
        ),
    ] = None,
    # VVZ filters: "Further criteria"
    number: Annotated[Nullable[str], Query(description="Unit number")] = None,
    title: Annotated[
        Nullable[str],
        Query(
            description="Title of the unit. It returns any results where the given title is included in the German or English unit title."
        ),
    ] = None,
    lecturer_id: Annotated[
        Nullable[Int64], Query(description="ID of the lecturer")
    ] = None,
    lecturer_name: Annotated[
        Nullable[str], Query(description="Name of the lecturer")
    ] = None,
    lecturer_surname: Annotated[
        Nullable[str], Query(description="Surname of the lecturer")
    ] = None,
    type: Annotated[
        Nullable[str], Query(description="Unit type: O, W+, W, E-, Z, Dr, etc.")
    ] = None,
    language: Annotated[
        Nullable[str], Query(description="Language of instruction")
    ] = None,
    periodicity: Annotated[
        Nullable[Periodicity],
        Query(description="Periodicity:0=ONETIME, 1=ANNUAL, 2=SEMESTER, 3=BIENNIAL"),
    ] = None,
    ects_min: Annotated[
        Nullable[float], Query(description="Minimum ECTS credits")
    ] = None,
    ects_max: Annotated[
        Nullable[float], Query(description="Maximum ECTS credits")
    ] = None,
    content_search: Annotated[
        Nullable[str], Query(description="Search within 'Catalogue data' on VVZ")
    ] = None,
) -> Sequence[int]:
    with tracer.start_as_current_span("list_units") as span:
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)
        if semkez:
            span.set_attribute("semkez", semkez)
        if section:
            span.set_attribute("section", section)
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
        query = await build_vvz_filter(session, select(LearningUnit.id), filters)
        results = (
            await session.exec(
                query.order_by(col(LearningUnit.id).asc()).offset(offset).limit(limit)
            )
        ).all()
        span.set_attribute("result_count", len(results))
        return results

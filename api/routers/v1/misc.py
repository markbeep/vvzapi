from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from opentelemetry import trace
from sqlalchemy.sql.functions import count
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import BaseModel, LearningUnit
from api.util.db import aget_session
from api.util.version import get_api_version

tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/misc", tags=["Miscellaneous"])


class MetricsResponse(BaseModel):
    total_learning_units: int
    total_courses: int
    total_lecturers: int
    total_sections: int


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    session: Annotated[AsyncSession, Depends(aget_session)],
) -> MetricsResponse:
    with tracer.start_as_current_span("get_metrics"):
        total_learning_units = (await session.exec(select(count("*")))).one()
        total_courses = (await session.exec(select(count("*")))).one()
        total_lecturers = (await session.exec(select(count("*")))).one()
        total_sections = (await session.exec(select(count("*")))).one()

        return MetricsResponse(
            total_learning_units=total_learning_units,
            total_courses=total_courses,
            total_lecturers=total_lecturers,
            total_sections=total_sections,
        )


class VersionResponse(BaseModel):
    version: str


@router.get("/version", response_model=VersionResponse)
async def get_version():
    with tracer.start_as_current_span("get_version"):
        return VersionResponse(version=get_api_version())


@router.get("/semesters", response_model=list[str])
async def list_semesters(
    session: Annotated[AsyncSession, Depends(aget_session)],
) -> Sequence[str]:
    """List all semesters for which there are learning units available."""
    with tracer.start_as_current_span("list_semesters") as span:
        semesters = (
            await session.exec(
                select(LearningUnit.semkez).distinct().order_by(LearningUnit.semkez)
            )
        ).all()
        span.set_attribute("result_count", len(semesters))
        return semesters

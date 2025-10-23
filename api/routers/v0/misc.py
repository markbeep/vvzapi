from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from sqlmodel import Session, func, select

from api.env import Settings
from api.models import BaseModel
from api.models import Course
from api.models import LearningUnit, Section
from api.models import Lecturer
from api.util.db import get_session
from api.util.version import get_api_version


router = APIRouter(prefix="/misc", tags=["Miscellaneous"])


class MetricsResponse(BaseModel):
    total_learning_units: int
    total_courses: int
    total_lecturers: int
    total_sections: int


@router.get("/metrics", response_model=MetricsResponse)
@cache(expire=Settings().cache_expiry)
async def get_metrics(
    session: Annotated[Session, Depends(get_session)],
) -> MetricsResponse:
    total_learning_units = session.exec(select(func.Count(LearningUnit.id))).one()
    total_courses = session.exec(select(func.Count(Course.number))).one()
    total_lecturers = session.exec(select(func.Count(Lecturer.id))).one()
    total_sections = session.exec(select(func.Count(Section.id))).one()

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
    return VersionResponse(version=get_api_version())


@router.get("/semesters", response_model=list[str])
@cache(expire=Settings().cache_expiry)
async def list_semesters(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[str]:
    """List all semesters for which there are learning units available."""
    semesters = session.exec(
        select(LearningUnit.semkez).distinct().order_by(LearningUnit.semkez)
    ).all()
    return semesters

from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.sql.functions import count
from sqlmodel import Session, select

from api.models import BaseModel
from api.models import LearningUnit
from api.util.db import get_session
from api.util.version import get_api_version


router = APIRouter(prefix="/misc", tags=["Miscellaneous"])


class MetricsResponse(BaseModel):
    total_learning_units: int
    total_courses: int
    total_lecturers: int
    total_sections: int


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    session: Annotated[Session, Depends(get_session)],
) -> MetricsResponse:
    total_learning_units = session.exec(select(count("*"))).one()
    total_courses = session.exec(select(count("*"))).one()
    total_lecturers = session.exec(select(count("*"))).one()
    total_sections = session.exec(select(count("*"))).one()

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
async def list_semesters(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[str]:
    """List all semesters for which there are learning units available."""
    semesters = session.exec(
        select(LearningUnit.semkez).distinct().order_by(LearningUnit.semkez)
    ).all()
    return semesters

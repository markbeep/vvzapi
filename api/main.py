from contextlib import asynccontextmanager
from typing import Annotated, Sequence
from fastapi import Depends, FastAPI, Query
from fastapi_cache import FastAPICache
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select
import uvicorn
import toml

from api.models.course import Course
from api.models.learning_unit import LearningUnit
from api.models.lecturer import Lecturer
from api.util.db import get_session
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

# get current version
with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)
    version = pyproject["project"]["version"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/units")
@cache(expire=60)
async def get_units(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[int]:
    return session.exec(select(LearningUnit.id).offset(offset).limit(limit)).all()


@app.get("/unit/{unit_id}")
@cache(expire=60)
async def get_unit(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> LearningUnit | None:
    return session.get(LearningUnit, unit_id)


class TitleResponse(BaseModel):
    id: int
    title: str


@app.get("/titles", response_model=list[TitleResponse])
@cache(expire=60)
async def get_titles(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return session.exec(
        select(LearningUnit.id, LearningUnit.title).offset(offset).limit(limit)
    ).all()


class MetricsResponse(BaseModel):
    semesters: list[str]
    total_learning_units: int
    total_courses: int
    total_lecturers: int
    version: str


@app.get("/metrics")
@cache(expire=60)
async def get_metrics(
    session: Annotated[Session, Depends(get_session)],
) -> MetricsResponse:
    semesters = session.exec(
        select(LearningUnit.semkez).distinct().order_by(LearningUnit.semkez)
    ).all()
    total_learning_units = session.exec(select(func.Count(LearningUnit.id))).one()
    total_courses = session.exec(select(func.Count(Course.id))).one()
    total_lecturers = session.exec(select(func.Count(Lecturer.id))).one()

    return MetricsResponse(
        semesters=list(semesters),
        total_learning_units=total_learning_units,
        total_courses=total_courses,
        total_lecturers=total_lecturers,
        version=version,
    )


if __name__ == "__main__":
    uvicorn.run(app, port=8000)

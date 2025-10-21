from typing import Annotated, Sequence
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from sqlmodel import Session, col, select

from api.env import Settings
from api.models.course import Course
from api.util.db import get_session

router = APIRouter(prefix="/course", tags=["Courses"])


@router.get("/get/{unit_id}", response_model=list[Course])
@cache(expire=Settings().cache_expiry)
async def get_courses(
    session: Annotated[Session, Depends(get_session)],
    unit_id: int,
) -> Sequence[Course]:
    query = (
        select(Course).where(Course.unit_id == unit_id).order_by(col(Course.id).asc())
    )
    return session.exec(query).all()

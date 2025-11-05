from typing import Annotated, Sequence
from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from api.models import Course
from api.util.db import get_session

router = APIRouter(prefix="/course", tags=["Courses"])


@router.get("/get/{unit_id}", response_model=list[Course])
async def get_courses(
    session: Annotated[Session, Depends(get_session)],
    unit_id: int,
) -> Sequence[Course]:
    query = (
        select(Course)
        .where(Course.unit_id == unit_id)
        .order_by(col(Course.number).asc())
    )
    return session.exec(query).all()

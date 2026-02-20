from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from opentelemetry import trace
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Course
from api.util.db import aget_session

tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/course", tags=["Courses"])


@router.get("/get/{unit_id}", response_model=list[Course])
async def get_courses(
    session: Annotated[AsyncSession, Depends(aget_session)],
    unit_id: int,
) -> Sequence[Course]:
    with tracer.start_as_current_span("get_courses") as span:
        span.set_attribute("unit_id", unit_id)
        query = (
            select(Course)
            .where(Course.unit_id == unit_id)
            .order_by(col(Course.number).asc())
        )
        results = (await session.exec(query)).all()
        span.set_attribute("result_count", len(results))
        return results

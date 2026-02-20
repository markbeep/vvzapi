from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from opentelemetry import trace
from sqlmodel import Session, col, select

from api.models import Lecturer
from api.util.db import get_session

tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/lecturer", tags=["Lecturers"])


@router.get("/get/{lecturer_id}", response_model=Lecturer | None)
async def get_lecturer(
    session: Annotated[Session, Depends(get_session)],
    lecturer_id: int,
) -> Lecturer | None:
    with tracer.start_as_current_span("get_lecturer") as span:
        span.set_attribute("lecturer_id", lecturer_id)
        return session.get(Lecturer, lecturer_id)


@router.get("/list", response_model=Sequence[Lecturer])
async def list_lecturers(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Lecturer]:
    with tracer.start_as_current_span("list_lecturers") as span:
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)
        query = (
            select(Lecturer)
            .offset(offset)
            .limit(limit)
            .order_by(col(Lecturer.id).asc())
        )
        results = session.exec(query).all()
        span.set_attribute("result_count", len(results))
        return results

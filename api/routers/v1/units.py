from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from sqlmodel import Session, col, select

from api.env import Settings
from api.models.learning_unit import LearningUnit
from api.util.db import get_session
from api.util.unit_filter import VVZFilters, build_query

router = APIRouter(prefix="/unit", tags=["Learning Units"])


@router.get("/get/{unit_id}", response_model=LearningUnit | None)
@cache(expire=Settings().cache_expiry)
async def get_unit(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> LearningUnit | None:
    return session.get(LearningUnit, unit_id)


class TitleResponse(BaseModel):
    id: int
    title: str | None


@router.get("/list", response_model=Sequence[TitleResponse])
@cache(expire=Settings().cache_expiry)
async def list_units(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    semkez: Annotated[str | None, Query()] = None,
    filters: VVZFilters = VVZFilters(),
) -> Sequence[TitleResponse]:
    build_query(select(LearningUnit.id, LearningUnit.title), filters)
    return [
        TitleResponse(id=unit[0], title=unit[1])
        for unit in session.exec(
            select(LearningUnit.id, LearningUnit.title)
            .offset(offset)
            .limit(limit)
            .order_by(col(LearningUnit.id).asc())
        ).all()
    ]

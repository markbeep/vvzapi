from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from sqlmodel import Session, col, select

from api.env import Settings
from api.models import LearningUnit
from api.util.db import get_session
from api.util.unit_filter import VVZFilters, build_vvz_filter, get_vvz_filters

router = APIRouter(prefix="/unit", tags=["Learning Units"])


@router.get("/get/{unit_id}", response_model=LearningUnit | None)
@cache(expire=Settings().cache_expiry)
async def get_unit(
    unit_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> LearningUnit | None:
    # TODO: return section ids unit is in
    return session.get(LearningUnit, unit_id)


class TitleResponse(BaseModel):
    id: int
    title: str | None


@router.get("/list", response_model=Sequence[TitleResponse])
@cache(expire=Settings().cache_expiry)
async def list_units(
    session: Annotated[Session, Depends(get_session)],
    filters: Annotated[VVZFilters, Depends(get_vvz_filters)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[TitleResponse]:
    query = build_vvz_filter(
        session, select(LearningUnit.id, LearningUnit.title), filters
    )
    return [
        TitleResponse(id=unit[0], title=unit[1])
        for unit in session.exec(
            query.offset(offset).limit(limit).order_by(col(LearningUnit.id).asc())
        ).all()
    ]

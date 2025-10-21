from typing import Annotated, Sequence
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select

from api.env import Settings
from api.models.learning_unit import Section, SectionBase, UnitSectionLink
from api.util.db import get_session
from api.util.sections import SectionLevel, get_child_sections, get_parent_sections

router = APIRouter(prefix="/section", tags=["Sections"])


@router.get("/list", response_model=list[Section])
@cache(expire=Settings().cache_expiry)
async def list_sections(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Section]:
    return session.exec(
        select(Section).offset(offset).limit(limit).order_by(col(Section.id).asc())
    ).all()


class LearningUnitType(BaseModel):
    id: Annotated[int, Field(description="ID of the learning unit")]
    type: str | None


class SectionUnitResponse(SectionBase):
    learning_units: list[LearningUnitType]
    parents: list[SectionLevel] = []
    children: list[SectionLevel] = []


@router.get("/get/{section_id}", response_model=SectionUnitResponse | None)
@cache(expire=Settings().cache_expiry)
async def get_section(
    session: Annotated[Session, Depends(get_session)],
    section_id: int,
) -> SectionUnitResponse | None:
    child_sections = get_child_sections(session, section_id)
    parent_sections = get_parent_sections(session, section_id)

    sections = session.get(Section, section_id)
    sub_units = session.exec(
        select(UnitSectionLink).where(
            col(UnitSectionLink.section_id).in_(
                [x.id for x in child_sections] + [section_id]
            )
        )
    ).all()

    return SectionUnitResponse.model_validate(
        sections,
        update={
            "learning_units": [
                LearningUnitType(id=unit.unit_id, type=unit.type) for unit in sub_units
            ],
            "children": child_sections,
            "parents": parent_sections,
        },
    )

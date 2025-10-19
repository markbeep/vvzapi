from typing import Annotated, Sequence
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlmodel import Session, col, select

from api.env import Settings
from api.models.learning_unit import (
    LearningUnit,
    Section,
    SectionBase,
    UnitSectionLink,
    UnitTypeEnum,
)
from api.util.db import get_session

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
    type: UnitTypeEnum | None


class SectionLevel(BaseModel):
    id: int
    level: int


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
    # Find all sections below the given section_id
    children_sql = """
        WITH RECURSIVE section_tree AS (
            SELECT id, parent_id, level
            FROM Section
            WHERE parent_id = :root_id
            UNION ALL
            SELECT s.id, s.parent_id, s.level
            FROM Section s
            INNER JOIN section_tree st ON s.parent_id = st.id
        )
        SELECT id, level FROM section_tree;
    """
    results = session.execute(text(children_sql), params={"root_id": section_id})
    child_sections = [
        SectionLevel(id=row[0], level=row[1]) for row in results.fetchall()
    ]
    parents_sql = """
        WITH RECURSIVE section_tree AS (
            SELECT id, parent_id, level
            FROM Section
            WHERE id = :root_id
            UNION ALL
            SELECT s.id, s.parent_id, s.level
            FROM Section s
            INNER JOIN section_tree st ON s.id = st.parent_id
        )
        SELECT id, level FROM section_tree WHERE id != :root_id;
    """
    results = session.execute(text(parents_sql), params={"root_id": section_id})
    parent_sections = [
        SectionLevel(id=row[0], level=row[1]) for row in results.fetchall()
    ]

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

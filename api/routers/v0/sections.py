from typing import Annotated, Sequence
from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field
from sqlmodel import Session, case, col, func, or_, select

from api.env import Settings
from api.models import Section, SectionBase, UnitSectionLink
from api.util.db import get_session
from api.util.sections import SectionLevel, get_child_sections, get_parent_sections

router = APIRouter(prefix="/section", tags=["Sections"])


@router.get("/list", response_model=list[int])
@cache(expire=Settings().cache_expiry)
async def list_sections(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    # VVZ filters
    semkez: Annotated[
        str | None,
        Query(
            description="Year + semester (Summer/Winter). Format is YYYY[S/W]. Example: 2025S, 2025W."
        ),
    ] = None,
    sort_lex: Annotated[
        bool,
        Query(
            description="Sort sections alphabetically in ascending order as is done on VVZ. Numbers are at the end. If disabled, sorts by section ID."
        ),
    ] = False,
    # Custom filters
    level: Annotated[int | None, Query(description="Level of the section")] = None,
    name_search: Annotated[
        str | None, Query(description="Search string for section names")
    ] = None,
    comment_search: Annotated[
        str | None, Query(description="Search string for section comments")
    ] = None,
    parent_id: Annotated[
        int | None, Query(description="Filter sections by **direct** parent section ID")
    ] = None,
) -> Sequence[int]:
    query = (
        select(
            Section.id,
            name := func.COALESCE(Section.name_english, Section.name),
        )
        .where(
            Section.semkez == semkez if semkez is not None else True,
            Section.level == level if level is not None else True,
            or_(
                col(Section.name).ilike(f"%{name_search}%"),
                col(Section.name_english).ilike(f"%{name_search}%"),
            )
            if name_search is not None
            else True,
            or_(
                col(Section.comment).ilike(f"%{comment_search}%"),
                col(Section.comment_english).ilike(f"%{comment_search}%"),
            )
            if comment_search is not None
            else True,
            Section.parent_id == parent_id if parent_id is not None else True,
        )
        .offset(offset)
        .limit(limit)
    )

    if sort_lex:
        query = query.order_by(
            case((name.is_not(None), 1), else_=0).desc(),  # null last
            col(Section.level).asc(),
            name.op("GLOB")("[^0-9]*").desc(),  # text before numeric
            func.LOWER(name).asc(),
        )
    else:
        query = query.order_by(col(Section.id).asc())

    return [section_id for section_id, _ in session.exec(query).all()]


class LearningUnitType(BaseModel):
    id: Annotated[int, Field(description="ID of the learning unit")]
    type: str | None


class SectionUnitResponse(SectionBase):
    learning_units: list[LearningUnitType]
    parents: list[SectionLevel] = []
    children: list[SectionLevel] = []


@router.get("/{section_id}/get", response_model=SectionUnitResponse | None)
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

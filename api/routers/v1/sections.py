from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from opentelemetry import trace
from pydantic import BaseModel, Field
from sqlmodel import case, col, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Section, SectionBase, UnitSectionLink
from api.util.db import aget_session
from api.util.sections import SectionLevel, get_child_sections, get_parent_sections

tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/section", tags=["Sections"])


@router.get("/list", response_model=list[int])
async def list_sections(
    session: Annotated[AsyncSession, Depends(aget_session)],
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
    with tracer.start_as_current_span("list_sections") as span:
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)
        span.set_attribute("sort_lex", sort_lex)
        if semkez:
            span.set_attribute("semkez", semkez)
        if level:
            span.set_attribute("level", level)
        if parent_id:
            span.set_attribute("parent_id", parent_id)

        name = (func.COALESCE(Section.name_english, Section.name),)
        query = (
            select(
                Section.id,
            )
            .where(
                Section.semkez == semkez if semkez is not None else True,
                Section.level == level if level is not None else True,
                or_(
                    col(Section.name).like(f"%{name_search}%"),
                    col(Section.name_english).like(f"%{name_search}%"),
                )
                if name_search is not None
                else True,
                or_(
                    col(Section.comment).like(f"%{comment_search}%"),
                    col(Section.comment_english).like(f"%{comment_search}%"),
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
                case((col(name).is_not(None), 1), else_=0).desc(),  # null last
                col(Section.level).asc(),
                col(name).op("GLOB")("[^0-9]*").desc(),  # text before numeric
                func.LOWER(name).asc(),
            )
        else:
            query = query.order_by(col(Section.id).asc())

        results = [section_id for section_id in (await session.exec(query)).all()]
        span.set_attribute("result_count", len(results))
        return results


class LearningUnitType(BaseModel):
    id: Annotated[int, Field(description="ID of the learning unit")]
    type: str | None


class SectionUnitResponse(SectionBase):
    learning_units: list[LearningUnitType]
    parents: list[SectionLevel] = []
    children: list[SectionLevel] = []


@router.get("/{section_id}/get", response_model=SectionUnitResponse | None)
async def get_section(
    session: Annotated[AsyncSession, Depends(aget_session)],
    section_id: int,
) -> SectionUnitResponse | None:
    with tracer.start_as_current_span("get_section") as span:
        span.set_attribute("section_id", section_id)
        child_sections = await get_child_sections(session, section_id)
        parent_sections = await get_parent_sections(session, section_id)

        sections = await session.get(Section, section_id)
        sub_units = (
            await session.exec(
                select(UnitSectionLink).where(
                    col(UnitSectionLink.section_id).in_(
                        [x.id for x in child_sections] + [section_id]
                    )
                )
            )
        ).all()

        span.set_attribute("child_sections_count", len(child_sections))
        span.set_attribute("parent_sections_count", len(parent_sections))
        span.set_attribute("sub_units_count", len(sub_units))

        return SectionUnitResponse.model_validate(
            sections,
            update={
                "learning_units": [
                    LearningUnitType(id=unit.unit_id, type=unit.type)
                    for unit in sub_units
                ],
                "children": child_sections,
                "parents": parent_sections,
            },
        )

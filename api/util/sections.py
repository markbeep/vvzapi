from typing import cast
from pydantic import BaseModel
from sqlalchemy import Label
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, select

from api.models import Section, UnitSectionLink


class SectionLevel(BaseModel):
    id: int
    level: int


def get_child_sections(
    session: Session,
    parent_section_id: int,
):
    # Find all sections below the given section_id
    base_stmt = select(Section.id, Section.parent_id, Section.level).where(
        Section.parent_id == parent_section_id
    )
    cte = base_stmt.cte("section_tree", recursive=True)
    Parent = aliased(Section)
    recursive = select(Parent.id, Parent.parent_id, Parent.level).join(
        cte, col(Parent.parent_id) == cte.c.id
    )
    cte = cte.union_all(recursive)

    results = session.exec(
        select(Section.id, Section.level).join(cte, col(Section.id) == cte.c.id)
    )

    child_sections = [
        SectionLevel(id=row[0], level=cast(int, row[1])) for row in results.fetchall()
    ]
    return child_sections


def get_parent_sections(session: Session, child_section_id: int):
    base_stmt = select(Section.id, Section.parent_id, Section.level).where(
        Section.id == child_section_id
    )
    cte = base_stmt.cte("section_tree", recursive=True)
    Parent = aliased(Section)
    recursive = select(Parent.id, Parent.parent_id, Parent.level).join(
        cte, col(Parent.id) == cte.c.parent_id
    )
    cte = cte.union_all(recursive)
    results = session.exec(
        select(Section.id, Section.level)
        .join(cte, col(Section.id) == cte.c.id)
        .where(Section.id != child_section_id)
    )

    parent_sections = [
        SectionLevel(id=row[0], level=row[1] or 0) for row in results.fetchall()
    ]
    return parent_sections


def get_parent_from_unit(unit_id: int | None = None):
    """Gets all sections, including parent sections, for a given unit ID"""
    base_stmt = select(Section.id, Section.parent_id).join(
        UnitSectionLink, col(UnitSectionLink.section_id) == Section.id
    )
    if unit_id is not None:
        base_stmt = base_stmt.where(UnitSectionLink.unit_id == unit_id)
    section_cte = base_stmt.cte("section_tree", recursive=True)
    ParentSection = aliased(Section)
    recursive_part = select(ParentSection.id, ParentSection.parent_id).join(
        section_cte, col(ParentSection.id) == section_cte.c.parent_id
    )
    section_cte = section_cte.union_all(recursive_part)
    return (
        select(Section)
        .join(section_cte, col(Section.id) == section_cte.c.id)
        .distinct()
    )


def concatenate_section_names():
    """Creates a CTE that concatenates section names from root to leaf."""
    anchor = select(
        Section.id,
        Section.parent_id,
        cast(Label[str | None], col(Section.name_english).label("path_en")),
        cast(Label[str | None], col(Section.name).label("path_de")),
    ).where(col(Section.parent_id).is_(None))

    cte = anchor.cte("section_paths", recursive=True)
    Parent = aliased(Section)
    recursive = select(
        Parent.id,
        Parent.parent_id,
        (cte.c.path_en + " > " + Parent.name_english).label("path_en"),
        (cte.c.path_de + " > " + Parent.name).label("path_de"),
    ).join(cte, col(Parent.parent_id) == cte.c.id)

    cte = cte.union_all(recursive)
    return select(cte.c.id, cte.c.path_en, cte.c.path_de)

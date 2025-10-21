from pydantic import BaseModel
from sqlmodel import Session, text


class SectionLevel(BaseModel):
    id: int
    level: int


def get_child_sections(
    session: Session,
    parent_section_id: int,
):
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
    results = session.execute(text(children_sql), params={"root_id": parent_section_id})
    child_sections = [
        SectionLevel(id=row[0], level=row[1]) for row in results.fetchall()
    ]
    return child_sections


def get_parent_sections(session: Session, child_section_id: int):
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
    results = session.execute(text(parents_sql), params={"root_id": child_section_id})
    parent_sections = [
        SectionLevel(id=row[0], level=row[1]) for row in results.fetchall()
    ]
    return parent_sections

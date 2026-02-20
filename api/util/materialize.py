from sqlalchemy import tuple_
from sqlmodel import Integer, Session, cast, col, delete, func, insert, select, text

from api.models import LearningUnit, Section, SectionPathView, UnitDepartmentView
from api.util.db import get_session
from api.util.sections import concatenate_section_names


def _update_section_path_view(session: Session):
    print("Updating section path view...")
    print("Deleting outdated section paths...")
    # delete outdated sections
    session.exec(
        delete(SectionPathView).where(
            col(SectionPathView.id).not_in(select(Section.id))
        )
    )

    SectionCTE = concatenate_section_names().subquery()

    print("Inserting/updating section paths...")
    # insert or update section paths
    insert_stmt = (
        insert(SectionPathView)
        .prefix_with("OR REPLACE")
        .from_select(
            ["id", "path_en", "path_de"],
            select(SectionCTE.c.id, SectionCTE.c.path_en, SectionCTE.c.path_de),
        )
    )
    # print(insert_stmt.compile(compile_kwargs={"literal_binds": True}))
    session.exec(insert_stmt)

    print("Section path view updated.")


def _update_unit_department_view(session: Session):
    print("Updating unit-department view...")
    json_each_query = (
        select(
            LearningUnit.id,
            cast(text("json_each.value"), Integer).label("unit_department_id"),
        )
        .select_from(LearningUnit, func.json_each(LearningUnit.departments))
        .where(col(LearningUnit.departments).is_not(None))
    )

    print("Deleting outdated unit-department links...")
    # delete outdated unit-department links
    session.exec(
        delete(UnitDepartmentView).where(
            tuple_(
                col(UnitDepartmentView.unit_id),
                col(UnitDepartmentView.department_id),
            ).not_in(json_each_query)
        )
    )

    print("Inserting/updating unit-department links...")
    # insert or update unit-department links
    insert_stmt = (
        insert(UnitDepartmentView)
        .prefix_with("OR REPLACE")
        .from_select(
            ["unit_id", "department_id"],
            json_each_query,
        )
    )
    session.exec(insert_stmt)

    print("Unit-department view updated.")


def update_materialized_views(session: Session):
    print("Updating materialized views...")
    _update_section_path_view(session)
    _update_unit_department_view(session)
    session.commit()


if __name__ == "__main__":
    with next(get_session()) as session:
        update_materialized_views(session)

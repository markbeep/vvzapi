from api.catalog.models import (
    BaseModel,
    Course,
    CourseLecturerLink,
    FinishedScrapingSemester,
    LatestSemkez,
    LearningUnit,
    Lecturer,
    Rating,
    Section,
    SectionPathView,
    UnitDepartmentView,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
    UnitTypeLegends,
)

DUMP_TABLES: tuple[type[BaseModel], ...] = (
    UnitExaminerLink,
    UnitLecturerLink,
    CourseLecturerLink,
    UnitSectionLink,
    LearningUnit,
    Section,
    UnitTypeLegends,
    Course,
    Lecturer,
    FinishedScrapingSemester,
    Rating,
    LatestSemkez,
    SectionPathView,
    UnitDepartmentView,
)


def get_dump_table_names() -> list[str]:
    """Table names served by the /dump export, see DUMP_TABLES."""
    # getattr: SQLModel declares __tablename__ as an InstrumentedAttribute, while the
    # runtime value of a `table=True` model is always the declared name string.
    return sorted(
        table_name
        for cls in DUMP_TABLES
        if isinstance(table_name := getattr(cls, "__tablename__", None), str)
    )

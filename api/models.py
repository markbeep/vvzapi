from enum import Enum
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class BaseModel(SQLModel):
    pass


class CatalogueData(BaseModel):
    abstract: str | None
    learning_objective: str | None
    content: str | None
    notice: str | None
    competencies: str | None
    lecture_notes: str | None
    literature: str | None
    other_data: list[str] = Field(sa_column=Column(JSON), default=[])


class ExamLecturerRelations(BaseModel, table=True):
    teaching_unit_id: int = Field(
        foreign_key="teachingunit.id", primary_key=True, ondelete="CASCADE"
    )
    lecturer_id: int = Field(
        foreign_key="lecturer.id", primary_key=True, ondelete="CASCADE"
    )


class PerformanceAssessment(BaseModel):
    # Two semester courses also list their full credits: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=192945&lang=en
    two_semester_credits: float | None
    programme_regulations: list[str] = Field(sa_column=Column(JSON), default=[])
    together_with_number: str | None

    # Credits are in infact actually floats, e.g. 1.5
    # For example: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=192834&semkez=2025W&ansicht=ALLE&lang=en
    ects_credits: float
    examiner_ids: list[int] = Field(sa_column=Column(JSON), default=[])
    assessment_type: str
    assessment_language: str
    repetition: str
    exam_block_of: list[str] = Field(sa_column=Column(JSON), default=[])

    mode: str | None
    additional_info: str | None
    written_aids: str | None
    distance: str | None
    digital: str | None
    update_note: str | None
    admission_requirement: str | None
    other_assessment: list[str] = Field(sa_column=Column(JSON), default=[])


class UnitTypeEnum(Enum):
    """www.vvz.ethz.ch/Vorlesungsverzeichnis/legendeStudienplanangaben.view?abschnittId=117361&semkez=2025W&lang=en"""

    O = "Compulsory"
    WPlus = "ElligibleRecommended"  # Eligible for credits and recommended
    W = "Elligible"  # Eligible for credits
    EMinus = "NotElligible"  # Recommended, not eligible for credits
    Z = "Outside"  # Courses outside the curriculum
    Dr = "Doctorate"  # Suitable for doctorate


class OfferedInRelations(BaseModel, table=True):
    """
    These are the relations from the "Offered in" section of a teaching unit
    """

    teaching_unit_id: int = Field(
        foreign_key="teachingunit.id", primary_key=True, ondelete="CASCADE"
    )
    section_id: int = Field(
        foreign_key="section.section_id", primary_key=True, ondelete="CASCADE"
    )
    type: UnitTypeEnum

    # TODO: fix this
    teaching_unit = Relationship(back_populates="offered_in_type")
    section = Relationship(back_populates="teaching_units_type")


class Section(BaseModel, table=True):
    """
    For example we have the following entries in the "Offered in" section:
    - Programme: Agricultural Sciences Bachelor
    - Section: First Year Examinations

    But if we go to [1] we can see that the full structure is as follows:
    - Agricultural Sciences Bachelor
        - 1. Semester
            - First Year Examinations

    Each of these entries has a sectionId (abschnittId), so we
    can handle them as their own section.

    [1] https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?abschnittId=118692&semkez=2025W&lang=en
    """

    section_id: int = Field(primary_key=True)
    name: str
    parent_id: str | None
    teaching_units: list["TeachingUnit"] = Relationship(
        back_populates="offered_in", link_model=OfferedInRelations
    )
    teaching_units_type: list[OfferedInRelations] = Relationship(
        back_populates="section"
    )


class SemesterEnum(Enum):
    HS = "HS"
    FS = "FS"


class TeachingUnit(PerformanceAssessment, CatalogueData, table=True):
    """What is commonly, but also confusingly, known as a "course". German translation is "Lerneinheit"."""

    id: int = Field(primary_key=True)
    number: str = Field(index=True)  # not unique because we store both languages
    year: int
    name: str = Field(index=True)
    semester: SemesterEnum
    text_language: str
    """en or de"""
    language: str
    courses: list["Course"] = Relationship(back_populates="teaching_unit")
    examiners: list["Lecturer"] = Relationship(
        back_populates="exams", link_model=ExamLecturerRelations
    )
    offered_in: list[Section] = Relationship(
        back_populates="teaching_units", link_model=OfferedInRelations
    )
    offered_in_type: list[OfferedInRelations] = Relationship(
        back_populates="teaching_unit"
    )

    class Config:  # pyright: ignore[reportIncompatibleVariableOverride]
        arbitrary_types_allowed = True

    def get_link(self) -> str:
        return f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId={self.id}&semkez={self.year}{self.semester.value}&ansicht=ALLE&lang={self.text_language}"


class CourseLecturerRelations(BaseModel, table=True):
    course_number: str = Field(
        foreign_key="course.number", primary_key=True, ondelete="CASCADE"
    )
    lecturer_id: int = Field(
        foreign_key="lecturer.id", primary_key=True, ondelete="CASCADE"
    )


class WeekdayEnum(Enum):
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6

    ByAppointment = 7


class CourseSlot(BaseModel):
    weekday: WeekdayEnum
    start_time: str  # "08:15"
    end_time: str  # "10:00"
    building: str
    room: str

    # If lectures only take place in the first/second half of a semester
    # https://ethz.ch/applications/teaching/en/applications/vvz/key.html
    first_half_semester: bool
    second_half_semester: bool
    two_weekly: bool


class CourseTypeEnum(Enum):
    V = "lecture"
    G = "lecture with exercise"
    U = "exercise"
    S = "seminar"
    K = "colloquium"
    P = "practical/laboratory course"
    A = "independent project"
    D = "diploma thesis"
    R = "revision course / private study"


class Course(BaseModel, table=True):
    """The time slots for when a teaching unit takes place"""

    number: str = Field(primary_key=True)
    name: str
    teaching_unit_id: int = Field(foreign_key="teachingunit.id", ondelete="CASCADE")
    teaching_unit: TeachingUnit = Relationship(back_populates="courses")
    slots: list[CourseSlot] = Field(sa_column=Column(JSON), default=[])
    type: CourseTypeEnum
    comments: str | None

    lecturers: list["Lecturer"] = Relationship(
        back_populates="courses", link_model=CourseLecturerRelations
    )


class Lecturer(BaseModel, table=True):
    id: int = Field(primary_key=True)
    firstname: str
    lastname: str
    golden_owl: bool = Field(default=False)

    courses: list[Course] = Relationship(
        back_populates="lecturers", link_model=CourseLecturerRelations
    )
    exams: list[TeachingUnit] = Relationship(
        back_populates="examiners", link_model=ExamLecturerRelations
    )

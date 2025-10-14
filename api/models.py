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


class ProgrammeSection(BaseModel):
    programme: str
    section: str
    type: UnitTypeEnum


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
    offered_in: list[ProgrammeSection] = Field(sa_column=Column(JSON), default=[])

    class Config:  # pyright: ignore[reportIncompatibleVariableOverride]
        arbitrary_types_allowed = True

    def get_link(self) -> str:
        return f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId={self.id}&semkez={self.year}{self.semester.value}&ansicht=ALLE&lang={self.text_language}"


class CourseLecturerRelations(BaseModel, table=True):
    course_id: int = Field(
        foreign_key="course.id", primary_key=True, ondelete="CASCADE"
    )
    lecturer_id: int = Field(
        foreign_key="lecturer.id", primary_key=True, ondelete="CASCADE"
    )


class WeekdayEnum(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


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

    id: int = Field(primary_key=True)
    number: str
    teaching_unit_id: int = Field(foreign_key="teachingunit.id", ondelete="CASCADE")
    teaching_unit: TeachingUnit = Relationship(back_populates="courses")
    weekday: WeekdayEnum
    start: str  # format of "08:15"
    end: str
    location: str
    type: CourseTypeEnum
    comments: str | None

    # If lectures only take place in the first/second half of a semester
    # https://ethz.ch/applications/teaching/en/applications/vvz/key.html
    first_half_semester: bool
    second_half_semester: bool
    two_weekly: bool

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

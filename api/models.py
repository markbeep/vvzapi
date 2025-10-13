from enum import Enum
from pydantic import BaseModel
from sqlalchemy import JSON, Column, Time
from sqlmodel import Field, Relationship, SQLModel


class SemesterEnum(Enum):
    HS = "HS"
    FS = "FS"


class UnitTypeEnum(Enum):
    """www.vvz.ethz.ch/Vorlesungsverzeichnis/legendeStudienplanangaben.view?abschnittId=117361&semkez=2025W&lang=en"""

    O = "Compulsory"
    WPlus = "ElligibleRecommended"  # Eligible for credits and recommended
    W = "Elligible"  # Eligible for credits
    EMinus = "NotElligible"  # Recommended, not eligible for credits
    Z = "Outside"  # Courses outside the curriculum
    Dr = "Doctorate"  # Suitable for doctorate


class TeachingUnit(SQLModel, table=True):
    id: int = Field(primary_key=True)
    year: int
    type: UnitTypeEnum
    number: str
    name: str
    semester: SemesterEnum
    language: str
    courses: list["Course"] = Relationship(back_populates="teaching_unit")

    # catalogue data
    abstract: str
    learning_objective: str
    content: str
    lecture_notes: str
    literature: str
    competencies: str

    # performance assessment
    examination_block: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    # TODO: courses can have multiple credit amounts. See https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=192945&lang=en
    ects_credits: int

    class Config:  # pyright: ignore[reportIncompatibleVariableOverride]
        arbitrary_types_allowed = True


class CourseLecturerRelations(SQLModel, table=True):
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


class Course(SQLModel, table=True):
    id: int = Field(primary_key=True)
    number: str
    teaching_unit_id: int = Field(foreign_key="teachingunit.id", ondelete="CASCADE")
    teaching_unit: TeachingUnit = Relationship(back_populates="courses")
    weekday: WeekdayEnum
    start: str  # format of "08:15"
    end: str
    location: str
    type: CourseTypeEnum

    # If lectures only take place in the first/second half of a semester
    # https://ethz.ch/applications/teaching/en/applications/vvz/key.html
    first_half_semester: bool
    second_half_semester: bool
    two_weekly: bool

    lecturers: list["Lecturer"] = Relationship(
        back_populates="courses", link_model=CourseLecturerRelations
    )


class Lecturer(SQLModel, table=True):
    id: int = Field(primary_key=True)
    firstname: str
    lastname: str

    courses: list[TeachingUnit] = Relationship(
        back_populates="lecturers", link_model=CourseLecturerRelations
    )

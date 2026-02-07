from __future__ import annotations

import time
from enum import Enum
from typing import override

from pydantic import BaseModel as PydanticBaseModel
from rapidfuzz import fuzz, process, utils
from sqlmodel import INTEGER, JSON, Column, Field, SQLModel

from api.util.pydantic_type import EnumList, PydanticType
from api.util.vvz_types import CourseTypeEnum, Group, TimeSlot


class BaseModel(SQLModel):
    pass


class Overwriteable:
    def overwrite_with(self, other: PydanticBaseModel):
        """
        Overwrites all fields that are not None from the other instance.
        Used to for example merge German and English versions of the same entity
        or overwrite for example a Lecturer with new data if their name changed.
        """
        if not isinstance(other, type(self)):
            return
        for field in other.model_fields_set:
            value_other = getattr(other, field)  # pyright: ignore[reportAny]
            setattr(self, field, value_other)


"""


LINK MODELS (many-to-many relationships)

We do not use foreign keys (especially for lecturers), because
it is possible for IDs to be linked at places of which no page exists.

For example on the course page of [1] we have a lecturer with ID 10072423 linked, but
there is no page for this lecturer [2].

[1] https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=193329&lang=de
[2] https://www.vvz.ethz.ch/Vorlesungsverzeichnis/dozent.view?dozide=10072423&semkez=2025W&lang=de

By not using foreign keys, we can also store links out of order.

"""


class UnitExaminerLink(BaseModel, table=True):
    unit_id: int = Field(primary_key=True)
    lecturer_id: int = Field(primary_key=True)


class UnitLecturerLink(BaseModel, table=True):
    unit_id: int = Field(primary_key=True)
    lecturer_id: int = Field(primary_key=True)


class CourseLecturerLink(BaseModel, table=True):
    course_number: str = Field(primary_key=True)
    course_semkez: str = Field(primary_key=True)
    lecturer_id: int = Field(primary_key=True)


class UnitSectionLink(BaseModel, table=True):
    unit_id: int = Field(primary_key=True)
    section_id: int = Field(primary_key=True)
    type: str | None = Field(default=None)
    type_id: int | None = Field(default=None)


"""


LEARNING UNITS / LECTURES

We use the literal translation of "Lerneinheit" for a clear distinction from "Course"
and also to avoid the similarity with "Lecturer".

"""


class Periodicity(Enum):
    """
    Angabe, in welchem Intervall die Lehrveranstaltung abgehalten wird.
    - 0 einmalige Veranstaltung (einmalig)
    - 1 jährlich wiederkehrende Veranstaltung (jährlich)
    - 2 2-jährlich wiederkehrende Veranstaltung (2-jährlich)
    """

    ONETIME = 0
    ANNUAL = 1
    SEMESTER = 2
    BIENNIAL = 3

    @override
    def __str__(self) -> str:
        if self == Periodicity.ONETIME:
            return "Onetime"
        elif self == Periodicity.ANNUAL:
            return "Yearly recurring"
        elif self == Periodicity.SEMESTER:
            return "Semesterly recurring"
        elif self == Periodicity.BIENNIAL:
            return "Every two years"
        return "Unknown"


class NamedURL(BaseModel):
    name: str
    url: str


class OccurenceEnum(Enum):
    """
    - 0 Veranstaltung findet dieses Jahr nicht statt (nein)
    - 1 Veranstaltung findet dieses Jahr statt (ja)
    - 2 Annuliert (Annuliert)
    """

    NO = 0
    YES = 1
    CANCELLED = 2


class Level(str, Enum):
    # NOTE: enum values should match the string. Might break reading/writing into DB otherwise
    BSC = "BSC"
    """Bachelor's Degree Program"""
    DZ = "DZ"
    """Didactics Certificate"""
    DS = "DS"
    """Diploma Programme"""
    DR = "DR"
    """Doctorate"""
    SHE = "SHE"
    """Teaching Diploma"""
    MSC = "MSC"
    """Master's Degree Program"""
    GS = "GS"
    """Mobility Students"""
    WBZ = "WBZ"
    """Advanced Studies (CAS, DAS)"""
    NDS = "NDS"
    """Master of Advanced Studies"""

    @override
    def __str__(self) -> str:
        return self.value

    def description(self) -> str:
        descriptions = {
            Level.BSC: "Bachelor's Degree Program",
            Level.DZ: "Didactics Certificate",
            Level.DS: "Diploma Programme",
            Level.DR: "Doctorate",
            Level.SHE: "Teaching Diploma",
            Level.MSC: "Master's Degree Program",
            Level.GS: "Mobility Students",
            Level.WBZ: "Advanced Studies (CAS, DAS)",
            Level.NDS: "Master of Advanced Studies",
        }
        return descriptions.get(self, "Unknown")

    @staticmethod
    def get(v: str | Level) -> Level:
        if isinstance(v, Level):
            return v
        return Level[v]


class Department(Enum):
    """This seems to be hardcoded on the VVZ website"""

    ARCHITECTURE = 1
    CIVIL_ENVIRONMENTAL_AND_GEOMATIC_ENGINEERING = 2
    MECHANICAL_AND_PROCESS_ENGINEERING = 3
    COMPUTER_SCIENCE = 5
    MANAGEMENT_TECHNOLOGY_AND_ECONOMICS = 7
    MATHEMATICS = 8
    PHYSICS = 9
    BIOLOGY = 11
    EARTH_AND_PLANETARY_SCIENCES = 13
    HUMANITIES_SOCIAL_AND_POLITICAL_SCIENCES = 17
    INFORMATION_TECHNOLOGY_AND_ELECTRICAL_ENGINEERING = 18
    MATERIALS = 19
    CHEMISTRY_AND_APPLIED_BIOSCIENCES = 20
    BIOSYSTEMS_SCIENCE_AND_ENGINEERING = 23
    HEALTH_SCIENCES_AND_TECHNOLOGY = 24
    ENVIRONMENTAL_SYSTEMS_SCIENCE = 25

    @staticmethod
    def get(v: str | int | Department) -> Department:
        if isinstance(v, Department):
            return v
        if isinstance(v, int) or v.isdigit():
            return Department(int(v))
        return Department[v]

    @override
    def __str__(self) -> str:
        return self.name.replace("_", " ").title()

    def short(self) -> str:
        short_names = {
            Department.ARCHITECTURE: "D-ARCH",
            Department.CIVIL_ENVIRONMENTAL_AND_GEOMATIC_ENGINEERING: "D-BAUG",
            Department.MECHANICAL_AND_PROCESS_ENGINEERING: "D-MAVT",
            Department.COMPUTER_SCIENCE: "D-INFK",
            Department.MANAGEMENT_TECHNOLOGY_AND_ECONOMICS: "D-MTEC",
            Department.MATHEMATICS: "D-MATH",
            Department.PHYSICS: "D-PHYS",
            Department.BIOLOGY: "D-BIOL",
            Department.EARTH_AND_PLANETARY_SCIENCES: "D-ERDW",
            Department.HUMANITIES_SOCIAL_AND_POLITICAL_SCIENCES: "D-GESS",
            Department.INFORMATION_TECHNOLOGY_AND_ELECTRICAL_ENGINEERING: "D-ITET",
            Department.MATERIALS: "D-MATL",
            Department.CHEMISTRY_AND_APPLIED_BIOSCIENCES: "D-CHAB",
            Department.BIOSYSTEMS_SCIENCE_AND_ENGINEERING: "D-BSSE",
            Department.HEALTH_SCIENCES_AND_TECHNOLOGY: "D-HEST",
            Department.ENVIRONMENTAL_SYSTEMS_SCIENCE: "D-USYS",
        }
        return short_names.get(self, "Unknown")

    @staticmethod
    def closest_match(name: str) -> Department | None:
        short_names = {
            "ARCH": Department.ARCHITECTURE,
            "BAUG": Department.CIVIL_ENVIRONMENTAL_AND_GEOMATIC_ENGINEERING,
            "MAVT": Department.MECHANICAL_AND_PROCESS_ENGINEERING,
            "INFK": Department.COMPUTER_SCIENCE,
            "MTEC": Department.MANAGEMENT_TECHNOLOGY_AND_ECONOMICS,
            "MATH": Department.MATHEMATICS,
            "PHYS": Department.PHYSICS,
            "BIOL": Department.BIOLOGY,
            "ERDW": Department.EARTH_AND_PLANETARY_SCIENCES,
            "GESS": Department.HUMANITIES_SOCIAL_AND_POLITICAL_SCIENCES,
            "ITET": Department.INFORMATION_TECHNOLOGY_AND_ELECTRICAL_ENGINEERING,
            "MATL": Department.MATERIALS,
            "CHAB": Department.CHEMISTRY_AND_APPLIED_BIOSCIENCES,
            "BSSE": Department.BIOSYSTEMS_SCIENCE_AND_ENGINEERING,
            "HEST": Department.HEALTH_SCIENCES_AND_TECHNOLOGY,
            "USYS": Department.ENVIRONMENTAL_SYSTEMS_SCIENCE,
        }
        for short_name, dept in short_names.items():
            if short_name in name.upper():
                return dept

        # fuzzy match with full name
        keys = list(str(x) for x in Department)
        if result := process.extractOne(
            name, keys, scorer=fuzz.WRatio, processor=utils.default_process
        ):
            matched_name, score, _ = result
            if score >= 80:
                return Department.get(matched_name.replace(" ", "_").upper())
        return None


class LearningUnit(BaseModel, Overwriteable, table=True):
    """
    This is the general learning unit type that includes all the information for a given course.

    This is what you see when you visit a VVZ unit: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=en&semkez=2025W&ansicht=ALLE&lerneinheitId=193444&

    We do not set any unique constraints, since it's possible for two courses to have the same number
    in the same semester. For example:
    - https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2005W&ansicht=ALLE&lerneinheitId=32830&lang=de
    - https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2005W&ansicht=ALLE&lerneinheitId=32831&lang=de
    """

    id: int = Field(primary_key=True)
    semkez: str
    """Semester in the format JJJJS, where JJJJ is the year and either S or W indicates the semester."""
    number: str | None = Field(default=None)
    """263-3010-00L type code. Check the `RE_CODE` to more details on the format."""
    title: str | None = Field(default=None)
    title_english: str | None = Field(default=None)
    levels: list[Level] = Field(default_factory=list, sa_column=Column(EnumList(Level)))
    """Levels of the learning unit, e.g., BSC, MSC, etc."""
    departments: list[Department] = Field(
        default_factory=list, sa_column=Column(EnumList(Department))
    )
    """Department offering this learning unit."""
    credits: float | None = Field(default=None)
    two_semester_credits: float | None = Field(default=None)
    literature: str | None = Field(default=None)
    literature_english: str | None = Field(default=None)
    objective: str | None = Field(default=None)
    """Learning objective or 'Lernziel' in German"""
    objective_english: str | None = Field(default=None)
    content: str | None = Field(default=None)
    content_english: str | None = Field(default=None)
    lecture_notes: str | None = Field(default=None)
    lecture_notes_english: str | None = Field(default=None)
    additional: str | None = Field(default=None)
    additional_english: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    """Comment that is also visible on the search page"""
    comment_english: str | None = Field(default=None)
    max_places: int | None = Field(default=None)
    """Max amount of places available for registration. Set to -1 if 'Limited number of places. Special selection procedure.'"""
    waitlist_end: str | None = Field(default=None)
    """Until when the waitlist will be kept. Format yyyy-mm-dd"""
    signup_end: str | None = Field(default=None)
    """Until when registration is possible. Format yyyy-mm-dd"""
    signup_start: str | None = Field(default=None)
    """From when on registration is possible. Format yyyy-mm-dd"""
    priority: str | None = Field(default=None)
    """Note about who gets priority for this course: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=en&semkez=2025W&ansicht=ALLE&lerneinheitId=193444&"""
    primary_target_group: list[str] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    """Who this course is intended for: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=en&semkez=2025W&ansicht=ALLE&lerneinheitId=193444&"""
    language: str | None = Field(default=None)
    abstract: str | None = Field(default=None)
    abstract_english: str | None = Field(default=None)
    competencies: dict[str, dict[str, str]] | None = Field(
        default=None, sa_column=Column(JSON)
    )
    competencies_english: dict[str, dict[str, str]] | None = Field(
        default=None, sa_column=Column(JSON)
    )
    regulations: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    written_aids: str | None = Field(default=None)
    """If written aids are allowed and in what format."""
    additional_info: str | None = Field(default=None)
    """Additional information about the exam."""
    exam_mode: str | None = Field(default=None)
    """Mode of the exam, e.g., 'written 180 minutes'."""
    exam_language: str | None = Field(default=None)
    exam_type: str | None = Field(default=None)
    """Type of the exam, e.g., 'session examination' or 'ungraded semester performance'"""
    exam_block: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    """What semester blocks the exam is part of."""
    digital: str | None = Field(default=None)
    """Note about whether the exam is digital or not."""
    distance_exam: str | None = Field(default=None)
    """Note about whether the exam can be taken as a distance exam."""
    repetition: str | None = Field(default=None)
    """Information about if and how the exam can be repeated."""
    groups: list[Group] = Field(default_factory=list, sa_column=Column(JSON))
    """Groups can have no slot nor any info: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=de&lerneinheitId=193540&semkez=2025W&ansicht=ALLE&"""
    groups_signup_end: str | None = Field(default=None)
    course_frequency: Periodicity | None = Field(default=None)
    learning_materials: dict[str, list[NamedURL]] | None = Field(
        default=None, sa_column=Column(PydanticType(dict[str, list[NamedURL]]))
    )
    """Links to learning materials provided for this learning unit."""
    occurence: OccurenceEnum | None = Field(default=None)
    general_restrictions: str | None = Field(default=None)
    """Extra notes on any restrictions for this learning unit."""
    scraped_at: int = Field(
        default_factory=lambda: int(time.time()),
        sa_column=Column(INTEGER, nullable=False),
    )

    def departments_as_str(self) -> str:
        return ", ".join([str(dep) for dep in self.departments])

    def departments_as_short_str(self) -> str:
        return ", ".join([dep.short() for dep in self.departments])

    def levels_as_str(self) -> str:
        return ", ".join([str(level) for level in self.levels])


"""


Section


"""


class SectionBase(BaseModel, Overwriteable):
    id: int = Field(primary_key=True)
    parent_id: int | None = Field(default=None)
    """Parent section ID for hierarchical sections."""
    semkez: str
    name: str | None = Field(default=None)
    name_english: str | None = Field(default=None)
    level: int | None = Field(default=None)
    comment: str | None = Field(default=None)
    comment_english: str | None = Field(default=None)
    scraped_at: int = Field(
        default_factory=lambda: int(time.time()),
        sa_column=Column(INTEGER, nullable=False),
    )


class Section(SectionBase, table=True):
    pass


"""


UNIT LEGENDS


"""


class UnitType(BaseModel):
    # www.vvz.ethz.ch/Vorlesungsverzeichnis/legendeStudienplanangaben.view?abschnittId=117361&semkez=2025W&lang=de
    type: str
    description: str


class UnitTypeLegends(BaseModel, Overwriteable, table=True):
    id: int = Field(primary_key=True)
    title: str
    semkez: str
    legend: list[UnitType] = Field(
        default_factory=list, sa_column=Column(PydanticType(list[UnitType]))
    )
    scraped_at: int = Field(
        default_factory=lambda: int(time.time()),
        sa_column=Column(INTEGER, nullable=False),
    )


"""


COURSES


"""


class CourseHourEnum(Enum):
    WEEKLY_HOURS = 1
    SEMESTER_HOURS = 2


# TODO: There are a few attributes listed on the SOAP docs, that could be hiding out in VVZ somewhere and missing on this model.
# https://www.bi.id.ethz.ch/soapvvz-2023-1/manual/SoapVVZ.pdf#page=18
class Course(BaseModel, Overwriteable, table=True):
    number: str = Field(primary_key=True)
    """263-3010-00L type code. Check the `RE_CODE` to more details on the format."""
    semkez: str = Field(primary_key=True)
    """Semester in the format JJJJS, where JJJJ is the year and either S or W indicates the semester."""
    # TODO: add foreign key back to unit_id if we need it = Field(foreign_key="learningunit.id", ondelete="CASCADE")
    unit_id: int = Field(primary_key=True)
    """Parent learning unit ID."""
    title: str | None = Field(default=None)
    """Designation of the course. No english translation available."""
    type: CourseTypeEnum | None = Field(default=None)
    """
    Course types can be missing/null, like here:
    https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?ansicht=ALLE&lerneinheitId=25212&semkez=2005W&lang=en
    """
    hours: float | None = Field(default=None)
    """Number of hours per week or semester."""
    hour_type: CourseHourEnum | None = Field(default=None)
    """Describes how to interpret the hours attribute."""
    comment: str | None = Field(default=None)
    """Comment underneath a course"""
    timeslots: list[TimeSlot] = Field(
        default_factory=list, sa_column=Column(PydanticType(list[TimeSlot]))
    )
    scraped_at: int = Field(
        default_factory=lambda: int(time.time()),
        sa_column=Column(INTEGER, nullable=False),
    )


"""


LECTURERS


"""


class Lecturer(BaseModel, Overwriteable, table=True):
    id: int = Field(primary_key=True)
    surname: str
    name: str
    title: str | None
    department: str
    scraped_at: int = Field(
        default_factory=lambda: int(time.time()),
        sa_column=Column(INTEGER, nullable=False),
    )

    @override
    def __str__(self) -> str:
        return f"{self.surname} {self.name}"


"""


MISCELLANEOUS


"""


class UnitChanges(BaseModel, table=True):
    """We keep track of changes that get applied to learning units"""

    id: int | None = Field(default=None, primary_key=True)
    unit_id: int
    changes: dict[str, object] = Field(sa_column=Column(JSON()))
    scraped_at: int
    """The scraped_at before the changes were applied"""


class FinishedScrapingSemester(BaseModel, table=True):
    """Keeps track of which semesters have been fully scraped already."""

    semkez: str = Field(primary_key=True)


class LastCleanup(BaseModel, table=True):
    """Keeps track of when the last cleanup of the scrapy cache was performed."""

    id: int | None = Field(default=None, primary_key=True)
    timestamp: int = Field(
        default_factory=lambda: int(time.time()),
        sa_column=Column(INTEGER, nullable=False),
    )

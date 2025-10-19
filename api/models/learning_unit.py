from enum import Enum
from pydantic import ConfigDict
from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Field, Column, Relationship
from api.util.pydantic_type import PydanticType
from api.util.types import CourseSlot
from api.models.base import BaseModel


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


class LearningUnit(BaseModel, table=True):
    """
    This is the general learning unit type that includes all the information for a given course.

    This is what you see when you visit a VVZ unit: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=en&semkez=2025W&ansicht=ALLE&lerneinheitId=193444&
    """

    __table_args__ = (UniqueConstraint("code", "semkez"),)

    id: int = Field(primary_key=True)
    code: str | None = Field(default=None)
    """263-3010-00L type code. Check the `RE_CODE` to more details on the format."""
    title: str | None = Field(default=None)
    title_english: str | None = Field(default=None)
    semkez: str = Field(max_length=5)
    """Semester in the format JJJJS, where JJJJ is the year and either S or W indicates the semester."""
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
    """Max amount of places available for registration"""
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
    groups: dict[str, CourseSlot | None] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    """Groups can have no slot nor any info: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=de&lerneinheitId=193540&semkez=2025W&ansicht=ALLE&"""
    course_frequency: Periodicity | None = Field(default=None)
    learning_materials: dict[str, list[NamedURL]] | None = Field(
        default=None, sa_column=Column(PydanticType(dict[str, list[NamedURL]]))
    )
    """Links to learning materials provided for this learning unit."""
    learning_materials_english: dict[str, list[NamedURL]] | None = Field(
        default=None,
        sa_column=Column(PydanticType(dict[str, list[NamedURL]])),
    )
    occurence: OccurenceEnum | None = Field(default=None)
    general_restrictions: str | None = Field(default=None)
    """Extra notes on any restrictions for this learning unit."""

    examiners: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    """IDs of persons who are examiners for this learning unit."""
    lecturers: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    """IDs of persons who are the general lecturers for this learning unit."""

    section_links: list["UnitSectionLink"] = Relationship(back_populates="unit")

    def overwrite_with(self, other: "LearningUnit"):
        """
        Overwrites all fields that are not None from the other instance.
        Used to merge german and english scraped data.
        """
        for field in other.model_fields_set:
            value_other = getattr(other, field)
            if value_other is not None:
                setattr(self, field, value_other)


class SectionBase(BaseModel):
    id: int = Field(primary_key=True)
    parent_id: int | None = Field(default=None)
    semkez: str
    name: str | None = Field(default=None)
    name_english: str | None = Field(default=None)
    level: int | None = Field(default=None)
    comment: str | None = Field(default=None)
    comment_english: str | None = Field(default=None)


class Section(SectionBase, table=True):
    unit_links: list["UnitSectionLink"] = Relationship(back_populates="section")

    def overwrite_with(self, other: "Section"):
        """
        Overwrites all fields that are not None from the other instance.
        Used to merge german and english scraped data.
        """
        for field in other.model_fields_set:
            value_other = getattr(other, field)
            if value_other is not None:
                setattr(self, field, value_other)


class UnitTypeEnum(Enum):
    """www.vvz.ethz.ch/Vorlesungsverzeichnis/legendeStudienplanangaben.view?abschnittId=117361&semkez=2025W&lang=en"""

    O = 0
    WPlus = 1  # Eligible for credits and recommended
    W = 2  # Eligible for credits
    EMinus = 3  # Recommended, not eligible for credits
    Z = 4  # Courses outside the curriculum
    Dr = 5  # Suitable for doctorate


class UnitSectionLink(BaseModel, table=True):
    unit_id: int = Field(
        primary_key=True, foreign_key="learningunit.id", ondelete="CASCADE"
    )
    section_id: int = Field(
        primary_key=True, foreign_key="section.id", ondelete="CASCADE"
    )
    type: UnitTypeEnum | None = Field(default=None)

    unit: "LearningUnit" = Relationship(back_populates="section_links")
    section: "Section" = Relationship(back_populates="unit_links")

from enum import Enum
from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Column, Field
from api.util.types import CourseSlot, CourseTypeEnum
from api.models.base import BaseModel
from api.util.pydantic_type import PydanticType


class CourseHourEnum(Enum):
    WEEKLY_HOURS = 1
    SEMESTER_HOURS = 2


# TODO: There are a few attributes listed on the SOAP docs, that could be hiding out in VVZ somewhere and missing on this model.
# https://www.bi.id.ethz.ch/soapvvz-2023-1/manual/SoapVVZ.pdf#page=18
class Course(BaseModel, table=True):
    __table_args__ = (UniqueConstraint("code", "semkez"),)

    id: int | None = Field(primary_key=True, default=None)
    unit_id: int = Field(foreign_key="learningunit.id", ondelete="CASCADE")
    """Parent learning unit ID."""
    code: str | None = Field(default=None)
    """263-3010-00L type code. Check the `RE_CODE` to more details on the format."""
    title: str | None = Field(default=None)
    """Designation of the course. No english translation available."""
    semkez: str | None = Field(default=None, max_length=5)
    """Semester in the format JJJJS, where JJJJ is the year and either S or W indicates the semester."""
    type: CourseTypeEnum | None = Field(default=None)
    hours: float | None = Field(default=None, max_digits=7, decimal_places=2)
    """Number of hours per week or semester."""
    hour_type: CourseHourEnum | None = Field(default=None)
    """Describes how to interpret the hours attribute."""
    comment: str | None = Field(default=None, max_length=1000)
    """Comment underneath a course"""
    timeslots: list[CourseSlot] = Field(
        default_factory=list, sa_column=Column(PydanticType(list[CourseSlot]))
    )
    # TODO: move to separate table
    lecturers: list[int] = Field(default_factory=list, sa_column=Column(JSON))

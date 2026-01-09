from enum import Enum
from typing import NewType, override
from pydantic import BaseModel


class WeekdayEnum(Enum):
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6
    # german
    Mo = 0
    Di = 1
    Mi = 2
    Do = 3
    Fr = 4
    Sa = 5
    So = 6

    ByAppointment = 7
    Date = 8
    Invalid = 9

    @override
    def __str__(self) -> str:
        if self == WeekdayEnum.Mon:
            return "Mon"
        elif self == WeekdayEnum.Tue:
            return "Tue"
        elif self == WeekdayEnum.Wed:
            return "Wed"
        elif self == WeekdayEnum.Thu:
            return "Thu"
        elif self == WeekdayEnum.Fri:
            return "Fri"
        elif self == WeekdayEnum.Sat:
            return "Sat"
        elif self == WeekdayEnum.Sun:
            return "Sun"
        elif self == WeekdayEnum.ByAppointment:
            return "By Appointment"
        elif self == WeekdayEnum.Date:
            return "Date"
        else:
            return "Invalid"


class TimeSlot(BaseModel):
    weekday: WeekdayEnum

    # some lectures have specific slots for certain dates
    # https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?ansicht=ALLE&lerneinheitId=194056&semkez=2025W&lang=en
    date: str | None = None  # "31.12"
    # start/end time can be missing for "External" lectures: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?ansicht=ALLE&lerneinheitId=182942&semkez=2024W&lang=en
    start_time: str | None  # "08:15"
    end_time: str | None  # "10:00"
    # building can be missing: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?ansicht=ALLE&lerneinheitId=183720&semkez=2024W&lang=de
    building: str | None
    floor: str | None
    room: str | None
    """
    Slots for groups can belong to a specific course, which is indicated
    by this flag. Alternatively this is also used to indicate the course
    a slot is part of.
    """

    # If lectures only take place in the first/second half of a semester
    # https://ethz.ch/applications/teaching/en/applications/vvz/key.html
    first_half_semester: bool
    second_half_semester: bool
    biweekly: bool


class Group(BaseModel):
    name: str
    timeslots: list[TimeSlot]
    number: str | None
    restriction: str | None


GroupSignupEnd = NewType("GroupSignupEnd", str)


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

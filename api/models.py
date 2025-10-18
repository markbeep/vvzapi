from enum import Enum
from pydantic import BaseModel


class UnitTypeEnum(Enum):
    """www.vvz.ethz.ch/Vorlesungsverzeichnis/legendeStudienplanangaben.view?abschnittId=117361&semkez=2025W&lang=en"""

    O = "Compulsory"
    WPlus = "ElligibleRecommended"  # Eligible for credits and recommended
    W = "Elligible"  # Eligible for credits
    EMinus = "NotElligible"  # Recommended, not eligible for credits
    Z = "Outside"  # Courses outside the curriculum
    Dr = "Doctorate"  # Suitable for doctorate


class SemesterEnum(Enum):
    HS = "HS"
    FS = "FS"


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


class CourseSlot(BaseModel):
    weekday: WeekdayEnum
    start_time: str  # "08:15"
    end_time: str  # "10:00"
    building: str
    floor: str
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

from pydantic import BaseModel

from api.models.learning_unit import Department, Level


class VVZFilters(BaseModel):
    # base
    semkez: str | None = None
    level: Level | None = None
    """Called 'Stufe' in VVZ. Can't scrape that """
    department: Department | None = None

    # "Structure"
    section: int | None = None
    """only a single section is required, unlike on VVZ"""

    # "Further criteria"
    number: str | None = None
    title: str | None = None
    lecturer_id: int | None = None
    lecturer_name: str | None = None
    lecturer_surname: str | None = None
    type: str | None = None
    language: str | None = None
    periodicity: int | None = None
    """
    - ONETIME = 0
    - ANNUAL = 1
    - SEMESTER = 2
    - BIENNIAL = 3
    """
    ects_min: float = 0
    ects_max: float = 999.0
    content_search: str | None = None
    """Called 'Catalogue data' on VVZ"""


def build_query[T](query: T, filters: VVZFilters) -> T: ...

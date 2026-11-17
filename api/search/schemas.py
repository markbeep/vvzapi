from collections.abc import Generator
from typing import override

from pydantic import BaseModel, Field

from api.catalog.models import LearningUnit
from api.catalog.semkez import semkez_to_comparable


class GroupedLearningUnits(BaseModel):
    number: str
    units: list[LearningUnit]
    rating: float | None = None

    @property
    def semkezs(self) -> list[str]:
        return sorted({unit.semkez for unit in self.units if unit.semkez})

    def latest_unit(self) -> LearningUnit | None:
        if not self.units:
            return None
        return max(self.units, key=lambda unit: semkez_to_comparable(unit.semkez))

    def with_semkez(self, semkez: str) -> LearningUnit | None:
        for unit in self.units:
            if unit.semkez == semkez:
                return unit
        return None

    @override
    def __iter__(self):
        for unit in sorted(
            self.units,
            key=lambda u: semkez_to_comparable(u.semkez),
            reverse=True,
        ):
            yield unit.semkez, unit


class SearchResponse(BaseModel):
    total: int = Field(
        description="Total amount of matching course numbers, not just those on this page."
    )
    results: dict[str, GroupedLearningUnits] = Field(
        description="Course number to all of its learning units across semesters."
    )
    parsed_query: str = Field(description="How the query was interpreted.")
    exec_time_ms: float = Field(description="Time spent executing the search.")

    @override
    def __iter__(self) -> Generator[tuple[str, GroupedLearningUnits]]:
        yield from self.results.items()

from datetime import date
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    refresh_html: bool = False
    """If html files, that are already present locally, should be refetched"""
    start_year: int = 2025
    # automatically include next year (if it exists)
    end_year: int = date.today().year + 1
    semester: str = "W"
    delay: float = 5.0

    def read_semesters(self) -> list[Literal["W", "S"]]:
        semesters: list[Literal["W", "S"]] = []
        for s in self.semester.split(","):
            s = s.strip()
            if s == "W" or s == "S":
                semesters.append(s)
        return semesters

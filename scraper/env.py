from datetime import date
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    refresh_html: bool = False
    """If html files, that are already cached locally, should be refetched"""

    # Semester settings only apply to newly scraped semesters
    # RESCRAPE_AMOUNT will overwrite this and cause only the last
    # two already scraped semesters to be rescraped
    start_year: int = date.today().year
    # automatically include next year (if it exists)
    end_year: int = date.today().year + 1
    semester: str = "W"

    delay: float = 5.0
    """Amount of seconds to at least wait between requests"""
    log_level: str = "INFO"
    log_append: bool = True
    disable_log_file: bool = False

    # delete valid cached files
    enable_rescrape: bool = False
    rescrape_amount: int = 500
    rescrape_age_seconds: int = 24 * 3600 * 14  # 14 days

    def read_semesters(self) -> list[Literal["W", "S"]]:
        semesters: list[Literal["W", "S"]] = []
        for s in self.semester.split(","):
            s = s.strip()
            if s == "W" or s == "S":
                semesters.append(s)  # ty: ignore[invalid-argument-type]
        return semesters

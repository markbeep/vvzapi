from typing import final
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    db_path: str = "data/db.sqlite"
    cache_expiry: int = 3600  # in seconds
    sitemap_expiry: int = 86400  # in seconds
    plausible_url: str | None = None
    """API event endpoint"""

    @property
    def zip_path(self) -> str:
        return self.db_path + ".zip"

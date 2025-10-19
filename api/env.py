from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_path: str = "data/db.sqlite"
    cache_expiry: int = 3600  # in seconds
    plausible_url: str | None = None
    """API event endpoint"""

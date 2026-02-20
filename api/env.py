from typing import final

from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    db_path: str = "data/db.sqlite"
    cache_expiry: int = 60 * 60 * 24 * 30  # in seconds (30 days)
    sitemap_expiry: int = 86400  # in seconds
    plausible_url: str | None = None
    """API event endpoint"""
    base_url: str = "https://vvzapi.ch"
    jaeger_endpoint: str | None = None
    """Jaeger OTLP endpoint (e.g., http://localhost:4317)"""
    otel_service_name: str = "vvzapi"
    """OpenTelemetry service name"""

    @property
    def zip_path(self) -> str:
        return self.db_path + ".zip"

    @property
    def vacuum_path(self) -> str:
        return self.db_path + ".vacuum"

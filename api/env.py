from typing import final

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class Clickhouse(BaseModel):
    """ClickHouse analytics store, plus how events are buffered on the way in."""

    url: str | None = None
    """ClickHouse HTTP interface, e.g. http://localhost:8123"""

    database: str = "vvzapi"
    user: str = "default"
    password: str | None = None

    queue_max: int = Field(default=20_000, gt=0)
    """Bounded so a ClickHouse outage cannot grow memory without limit."""

    flush_interval_seconds: float = Field(default=1.0, gt=0)
    """How often queued events are written out."""

    max_rows_per_insert: int = Field(default=5_000, gt=0)
    """ClickHouse dislikes huge single inserts, so batches are split at this size."""


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="_",
    )

    db_path: str = "data/db.sqlite"
    meta_db_path: str = "data/meta_db.sqlite"
    cache_expiry: int = 60 * 60 * 24 * 30  # in seconds (30 days)
    sitemap_expiry: int = 86400  # in seconds
    plausible_url: str | None = None
    """API event endpoint"""
    base_url: str = "https://vvzapi.ch"
    jaeger_endpoint: str | None = None
    """Jaeger OTLP endpoint (e.g., http://localhost:4317)"""
    otel_service_name: str = "vvzapi"
    """OpenTelemetry service name"""

    clickhouse: Clickhouse = Clickhouse()

    flag_webhook: str | None = None
    """Endpoint to send webhooks to if a unit is flagged"""

    @property
    def zip_path(self) -> str:
        return self.db_path + ".zip"

    @property
    def vacuum_path(self) -> str:
        return self.db_path + ".vacuum"

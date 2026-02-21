from __future__ import annotations

import hashlib
import secrets
import time

import httpx

from api.env import Settings


class IPHasher:
    def __init__(self, reset_interval: int = 3600):
        self.init_ts: float = time.time()
        self.salt: str | None = None
        self.reset_interval: int = reset_interval

    def hash_ip(self, ip: str):
        """GDPR compliant hiding of the IP"""
        if self.salt is None or time.time() - self.init_ts > self.reset_interval:
            self.salt = secrets.token_hex(16)
            self.init_ts = time.time()
        return hashlib.sha256((ip + self.salt).encode()).hexdigest()


hasher = IPHasher()


def _escape_tag_value(value: str) -> str:
    """Escape tag values for InfluxDB line protocol"""
    return value.replace(",", r"\,").replace("=", r"\=").replace(" ", r"\ ")


def _escape_field_value(value: str) -> str:
    """Escape field values for InfluxDB line protocol"""
    return value.replace('"', r"\"").replace("\\", r"\\")


def _build_line_protocol(
    measurement: str,
    tags: dict[str, str],
    fields: dict[str, str | int | float | bool],
    timestamp: int | None = None,
) -> str:
    """Build InfluxDB line protocol string"""
    # Measurement name
    line = _escape_tag_value(measurement)

    # Tags (optional)
    if tags:
        tag_strings = [
            f"{_escape_tag_value(k)}={_escape_tag_value(str(v))}"
            for k, v in sorted(tags.items())
            if v and str(v).strip()
        ]
        if tag_strings:
            line += "," + ",".join(tag_strings)

    # Fields (required)
    field_strings: list[str] = []
    for k, v in fields.items():
        escaped_key = _escape_tag_value(k)
        if isinstance(v, bool):
            field_strings.append(f"{escaped_key}={str(v).lower()}")
        elif isinstance(v, int):
            field_strings.append(f"{escaped_key}={v}i")
        elif isinstance(v, float):
            field_strings.append(f"{escaped_key}={v}")
        else:
            escaped_value = _escape_field_value(str(v))
            field_strings.append(f'{escaped_key}="{escaped_value}"')

    if not field_strings:
        # At least one field is required
        field_strings.append("value=1i")

    line += " " + ",".join(field_strings)

    # Timestamp (optional, nanoseconds)
    if timestamp is not None:
        line += f" {timestamp}"

    return line


async def send_to_influxdb(
    measurement: str,
    tags: dict[str, str] | None = None,
    fields: dict[str, str | int | float | bool] | None = None,
    timestamp: int | None = None,
) -> None:
    """Send analytics data to InfluxDB using line protocol"""
    settings = Settings()
    if not settings.influxdb_url:
        return

    tags = tags or {}
    fields = fields or {}

    # Use current time in nanoseconds if not provided
    if timestamp is None:
        timestamp = int(time.time() * 1_000_000_000)

    line = _build_line_protocol(measurement, tags, fields, timestamp)

    headers = {"Content-Type": "text/plain; charset=utf-8"}
    if settings.influxdb_token:
        headers["Authorization"] = f"Token {settings.influxdb_token}"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                settings.influxdb_url,
                content=line,
                headers=headers,
                timeout=5,
            )
    except Exception:
        pass

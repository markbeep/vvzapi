"""merge legacy meta database

Revision ID: fa7834bf8f88
Revises: bd150ba2a167
Create Date: 2026-10-10 14:56:09.507453

The Scrapy cache used to live in its own database (data/meta_db.sqlite, see
`Settings.meta_db_path`). Its tables are part of the main database now, so whatever the
standalone file still holds is copied over and the file is removed. Without the copy the
next scrape would refetch every page it had cached.
"""
# pyright: reportAny=false, reportExplicitAny=false

import logging
from pathlib import Path
from typing import Any, Sequence, Union

from sqlalchemy import Connection, create_engine, inspect, text

from alembic import op
from api.env import Settings

# revision identifiers, used by Alembic.
revision: str = "fa7834bf8f88"
down_revision: Union[str, Sequence[str], None] = "bd150ba2a167"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

# The schema the standalone meta database was left in when it was retired.
LEGACY_TABLES: dict[str, tuple[str, ...]] = {
    "httpcache": ("url", "status_code", "body", "headers", "scraped_at", "flagged"),
    "lastcleanup": ("id", "timestamp"),
}

# Cached response bodies are large, so the copy is streamed in bounded batches instead of
# being materialised: both entrypoints run this migration before starting the app, and a
# cache of several gigabytes must not have to fit in memory.
BATCH_ROWS = 200
BATCH_BYTES = 8 * 1024 * 1024


def _copy(
    legacy: Connection, target: Connection, table: str, columns: tuple[str, ...]
) -> bool:
    """Copy one legacy table into the main database.

    Returns whether the legacy rows are accounted for in the main database, i.e. whether
    removing the legacy file cannot lose cache entries.
    """
    if table not in set(inspect(legacy).get_table_names()):
        logger.warning("Legacy cache has no %s table, keeping the legacy file", table)
        return False

    present = {column["name"] for column in inspect(legacy).get_columns(table)}
    missing = [column for column in columns if column not in present]
    if missing:
        logger.warning(
            "Legacy %s table lacks %s, keeping the legacy file",
            table,
            ", ".join(missing),
        )
        return False

    if target.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one():
        # Existing rows were not proven to come from the legacy file, so nothing in the
        # legacy table is known to be redundant.
        logger.warning("%s already holds rows, keeping the legacy file", table)
        return False

    quoted = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join(f":{column}" for column in columns)
    insert = text(f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})')
    expected = legacy.exec_driver_sql(f'SELECT COUNT(*) FROM "{table}"').scalar_one()

    result = legacy.exec_driver_sql(f'SELECT {quoted} FROM "{table}"')
    batch: list[dict[str, Any]] = []
    batch_bytes = 0
    while rows := result.fetchmany(BATCH_ROWS):
        for row in rows:
            record = dict(zip(columns, row))
            batch.append(record)
            batch_bytes += sum(
                len(value)
                for value in record.values()
                if isinstance(value, bytes | str)
            )
        if batch_bytes >= BATCH_BYTES:
            target.execute(insert, batch)
            batch, batch_bytes = [], 0
    if batch:
        target.execute(insert, batch)

    copied = target.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
    if copied != expected:
        raise RuntimeError(f"copied {copied} of {expected} {table} rows")
    logger.info("Copied %d %s rows out of the legacy cache", copied, table)
    return True


def upgrade() -> None:
    """Upgrade schema."""
    legacy_path = Path(Settings().meta_db_path)
    if not legacy_path.exists():
        return

    legacy_engine = create_engine(f"sqlite+pysqlite:///{legacy_path}")
    target = op.get_bind()
    merged = True
    with legacy_engine.connect() as legacy:
        for table, columns in LEGACY_TABLES.items():
            merged &= _copy(legacy, target, table, columns)
    legacy_engine.dispose()

    if not merged:
        logger.warning(
            "Some cache entries could not be merged, leaving %s in place", legacy_path
        )
        return

    legacy_path.unlink()
    logger.info("Deleted the merged legacy cache at %s", legacy_path)


def downgrade() -> None:
    """Downgrade schema."""
    # The legacy file is not restored: its rows are still in the main database, and an
    # old deployment would only create an empty cache at Settings.meta_db_path anyway.

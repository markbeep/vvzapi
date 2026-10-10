"""import scrapy cache out of the data database

Revision ID: 22d3e359b4e7
Revises: bd150ba2a167
Create Date: 2026-10-10 20:05:00.000000

Release 1.13.0 briefly moved the Scrapy cache into the data database (data/db.sqlite)
and deleted the standalone file (data/meta_db.sqlite, see `Settings.meta_db_path`). That
made the scraper's cache writes contend with the API's reads on one file, so the cache is
its own database again. This migration merges whatever the data database still holds into
the cache database, keeping the cache's own copy of any row both databases have; the
data-database migration `alembic/versions/51ea83d2f050_drop_meta_tables.py` then drops
those tables once it has confirmed the cache database holds every row. Without the merge
the next scrape would refetch every page it had cached.

The two migrations are ordered: the cache entrypoints run `meta_db` before `data_db` so
the rows are read before they are dropped.
"""
# pyright: reportAny=false, reportExplicitAny=false

import logging
from pathlib import Path
from typing import Any, Sequence, Union

from sqlalchemy import Connection, create_engine, inspect, text

from alembic import op
from api.env import Settings

# revision identifiers, used by Alembic.
revision: str = "22d3e359b4e7"
down_revision: Union[str, Sequence[str], None] = "bd150ba2a167"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

# The tables the merged data database may still hold, in cache order.
SOURCE_TABLES: dict[str, tuple[str, ...]] = {
    "httpcache": ("url", "status_code", "body", "headers", "scraped_at", "flagged"),
    "lastcleanup": ("id", "timestamp"),
}

# Cached response bodies are large, so the copy is streamed in bounded batches instead of
# being materialised: the entrypoints run this migration before starting the app, and a
# cache of several gigabytes must not have to fit in memory.
BATCH_ROWS = 200
BATCH_BYTES = 8 * 1024 * 1024


def _copy(
    source: Connection, target: Connection, table: str, columns: tuple[str, ...]
) -> None:
    """Merge one table from the data database into the cache database.

    Both databases may hold rows, so the tables are merged on their primary key (`url`/`id`)
    instead of one being treated as authoritative: rows the cache database already has are
    kept, and rows only the data database has are added. After this every source row exists
    in the cache database, which is what the drop in `alembic/versions/51ea83d2f050` relies
    on.
    """
    if table not in set(inspect(source).get_table_names()):
        # Nothing was merged into the data database (fresh install, or already split).
        return

    present = {column["name"] for column in inspect(source).get_columns(table)}
    missing = [column for column in columns if column not in present]
    if missing:
        logger.warning(
            "Data database %s table lacks %s, skipping", table, ", ".join(missing)
        )
        return

    quoted = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join(f":{column}" for column in columns)
    # `ON CONFLICT DO NOTHING` rather than `INSERT OR IGNORE`: both skip primary-key
    # duplicates, but `OR IGNORE` would also swallow NOT NULL/CHECK violations and drop rows.
    insert = text(
        f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
    )
    expected = source.exec_driver_sql(f'SELECT COUNT(*) FROM "{table}"').scalar_one()
    before = target.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()

    result = source.exec_driver_sql(f'SELECT {quoted} FROM "{table}"')
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

    after = target.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
    inserted = after - before
    if inserted > expected:
        raise RuntimeError(
            f"inserted {inserted} rows for {expected} {table} source rows"
        )
    # Every skipped row conflicted on the primary key, so every source row now exists in the
    # cache database and the data database copy of it is redundant.
    logger.info(
        "Merged %d of %d %s rows out of the data database", inserted, expected, table
    )


def upgrade() -> None:
    """Upgrade schema."""
    source_path = Path(Settings().db_path)
    if not source_path.exists():
        return

    source_engine = create_engine(f"sqlite+pysqlite:///{source_path}")
    target = op.get_bind()
    with source_engine.connect() as source:
        for table, columns in SOURCE_TABLES.items():
            _copy(source, target, table, columns)
    source_engine.dispose()


def downgrade() -> None:
    """Downgrade schema."""
    # The rows stay in the cache database: the data-database migration that re-merges
    # them recreates the tables itself, and copying back here would duplicate the cache.

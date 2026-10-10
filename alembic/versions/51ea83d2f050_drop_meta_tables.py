"""drop the scrapy cache tables from the data database

Revision ID: 51ea83d2f050
Revises: fa7834bf8f88
Create Date: 2026-10-10 20:05:00.000000

The Scrapy cache lives in its own database again (`Settings.meta_db_path`); the
`meta_db` migration `alembic/meta_versions/22d3e359b4e7_import_from_data_database.py`
merges the rows out of here first, and the cache entrypoints run `meta_db` before
`data_db`. This migration drops the tables that release 1.13.0 merged in. Both drops are
conditional: a fresh install (or one that never ran the merge) has neither table.

Alembic cannot order the two namespaces against each other (`depends_on` only resolves
within one version directory), so the drop verifies the merge itself and refuses to drop a
table whose rows the cache database does not hold. That also covers an import that was
skipped because the source table lacks a column the merge expects.
"""

from pathlib import Path
from typing import Sequence, Union, cast

from sqlalchemy import Connection, create_engine, inspect, text

from alembic import op
from api.env import Settings

# revision identifiers, used by Alembic.
revision: str = "51ea83d2f050"
down_revision: Union[str, Sequence[str], None] = "fa7834bf8f88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MERGED_TABLES = ("httpcache", "lastcleanup")
_MERGE_HINT = "run `alembic -n meta_db upgrade heads` first"


def _row_count(connection: Connection, table: str) -> int:
    return cast(
        int, connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
    )


def _assert_cache_database_holds(connection: Connection, tables: Sequence[str]) -> None:
    """Refuse to drop rows the cache database has not taken over.

    `22d3e359b4e7` merges every source row into the cache database, so the cache must hold at
    least as many rows as the data database. Fewer rows - or no cache database at all - means
    the merge has not run (or was skipped), and dropping here would destroy the only copy of
    the cache. The comparison assumes nothing is evicting cache rows concurrently, which
    holds for the entrypoints: they migrate before the application starts.
    """
    cache_path = Path(Settings().meta_db_path)
    if not cache_path.exists():
        raise RuntimeError(f"{cache_path} does not exist; {_MERGE_HINT}")

    cache_engine = create_engine(f"sqlite+pysqlite:///{cache_path}")
    try:
        with cache_engine.connect() as cache:
            cache_tables = set(inspect(cache).get_table_names())
            for table in tables:
                source_rows = _row_count(connection, table)
                if not source_rows:
                    continue
                if table not in cache_tables:
                    raise RuntimeError(
                        f"{cache_path} has no {table} table, but the data database holds {source_rows} rows; {_MERGE_HINT}"
                    )
                cache_rows = _row_count(cache, table)
                if cache_rows < source_rows:
                    raise RuntimeError(
                        f"{cache_path} holds {cache_rows} of the {source_rows} {table} rows in the data database; {_MERGE_HINT}"
                    )
    finally:
        cache_engine.dispose()


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    existing = set(inspect(connection).get_table_names())
    tables = [table for table in MERGED_TABLES if table in existing]
    if tables:
        _assert_cache_database_holds(connection, tables)
    for table in tables:
        op.drop_table(table)


def downgrade() -> None:
    """Downgrade schema."""
    # The tables belong to the cache database now; re-merging them is not supported.

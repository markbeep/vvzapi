"""merge legacy meta database

Revision ID: fa7834bf8f88
Revises: bd150ba2a167
Create Date: 2026-10-10 14:56:09.507453

Superseded. Release 1.13.0 merged the Scrapy cache (data/meta_db.sqlite) into the data
database here; that was reverted because the scraper's cache writes then contended with
the API's reads on a single file. The revision is kept so databases that already recorded
it still resolve their revision chain, but it no longer copies or deletes anything. The
cache is imported back into its own database by
`alembic/meta_versions/22d3e359b4e7_import_from_data_database.py`, and the merged tables
are dropped by `alembic/versions/51ea83d2f050_drop_meta_tables.py`.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "fa7834bf8f88"
down_revision: str | Sequence[str] | None = "bd150ba2a167"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""

"""add flagged (superseded)

Revision ID: 357b241a4250
Revises: c28cde0a90db
Create Date: 2026-09-15 14:36:06.073737

This is a Scrapy-cache (meta) database revision. Release 1.13.0 briefly moved it into the
data database's history; the cache has its own database again, so the schema lives in
`alembic/meta_versions/`. The revision is kept as a no-op so that databases migrated by
1.13.0 can still resolve their revision chain.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "357b241a4250"
down_revision: str | Sequence[str] | None = "c28cde0a90db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""

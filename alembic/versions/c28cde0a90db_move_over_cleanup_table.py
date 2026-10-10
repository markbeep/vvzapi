"""move over cleanup table (superseded)

Revision ID: c28cde0a90db
Revises: fd345d2b7d78
Create Date: 2026-02-27 19:08:43.207368

This is a Scrapy-cache (meta) database revision. Release 1.13.0 briefly moved it into the
data database's history; the cache has its own database again, so the schema lives in
`alembic/meta_versions/`. The revision is kept as a no-op so that databases migrated by
1.13.0 can still resolve their revision chain.
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c28cde0a90db"
down_revision: Union[str, Sequence[str], None] = "fd345d2b7d78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""

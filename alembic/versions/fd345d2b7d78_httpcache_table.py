"""httpcache table (superseded)

Revision ID: fd345d2b7d78
Revises: 33e0846c3903
Create Date: 2026-02-27 17:45:49.644585

This is a Scrapy-cache (meta) database revision. Release 1.13.0 briefly moved it into the
data database's history; the cache has its own database again, so the schema lives in
`alembic/meta_versions/`. The revision is kept as a no-op so that databases migrated by
1.13.0 can still resolve their revision chain (their `alembic_version` may point at
`fa7834bf8f88`, whose ancestry includes these revisions).
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "fd345d2b7d78"
down_revision: Union[str, Sequence[str], None] = "33e0846c3903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""

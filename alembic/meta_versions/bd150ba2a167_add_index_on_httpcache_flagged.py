"""add index on httpcache.flagged

Revision ID: bd150ba2a167
Revises: 357b241a4250
Create Date: 2026-09-15 14:36:06.073737

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bd150ba2a167"
down_revision: Union[str, Sequence[str], None] = "357b241a4250"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Plain (non-batch) index creation: `httpcache` is a multi-GB cache table and a
    # batch operation would rebuild it. `flagged IS true` cannot use this index, but
    # `flagged = true` can, which is what the unit page queries with.
    op.create_index(op.f("ix_httpcache_flagged"), "httpcache", ["flagged"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_httpcache_flagged"), table_name="httpcache")

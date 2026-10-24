"""delete units with null numbers

Revision ID: b6c0d8f67343
Revises: 28d83f5b9096
Create Date: 2026-02-20 11:43:40.714941

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6c0d8f67343"
down_revision: str | Sequence[str] | None = "28d83f5b9096"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            """
            DELETE FROM learningunit
            WHERE number IS NULL
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""

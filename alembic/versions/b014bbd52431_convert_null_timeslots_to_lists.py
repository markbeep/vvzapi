"""convert null timeslots to lists

Revision ID: b014bbd52431
Revises: 2c332002ee3f
Create Date: 2026-05-07 13:13:14.913937

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b014bbd52431"
down_revision: Union[str, Sequence[str], None] = "2c332002ee3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            """
            UPDATE course
            SET timeslots = '[]'
            WHERE timeslots = 'null'
            """
        )
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

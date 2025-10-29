"""rename lectures directory

Revision ID: 469a31ddd9b4
Revises: dc051fb507e8
Create Date: 2025-10-29 16:26:24.142837

"""

from pathlib import Path
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "469a31ddd9b4"
down_revision: Union[str, Sequence[str], None] = "dc051fb507e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    p = Path(".scrapy/httpcache/lectures")
    if p.exists() and p.is_dir():
        p.rename(Path(".scrapy/httpcache/units"))


def downgrade() -> None:
    """Downgrade schema."""
    pass

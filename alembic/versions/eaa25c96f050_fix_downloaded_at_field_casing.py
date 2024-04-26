"""Fix downloaded_at field casing

Revision ID: eaa25c96f050
Revises: 027e32814456
Create Date: 2024-03-24 23:39:27.569187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'eaa25c96f050'
down_revision: Union[str, None] = '027e32814456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('download', 'downloadedAt', new_column_name="downloaded_at")


def downgrade() -> None:
    op.alter_column('download', 'downloaded_at', new_column_name="downloadedAt")

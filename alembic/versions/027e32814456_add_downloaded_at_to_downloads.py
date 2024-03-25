"""Add downloaded at to downloads

Revision ID: 027e32814456
Revises: d4bcebf28361
Create Date: 2024-03-24 23:08:11.369717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '027e32814456'
down_revision: Union[str, None] = 'd4bcebf28361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('download', sa.Column('downloadedAt', sa.DateTime(), server_default=sa.text('now()'), nullable=False))


def downgrade() -> None:
    op.drop_column('download', 'downloadedAt')
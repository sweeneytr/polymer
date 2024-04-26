"""Add mmf token table

Revision ID: af65a1990f8a
Revises: eaa25c96f050
Create Date: 2024-04-25 19:51:27.007081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af65a1990f8a'
down_revision: Union[str, None] = 'eaa25c96f050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('mmf',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('access_token', sa.String(), nullable=False),
    sa.Column('access_exp', sa.DateTime(), nullable=False),
    sa.Column('refresh_token', sa.String(), nullable=False),
    sa.Column('refresh_exp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('mmf')

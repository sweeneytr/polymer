"""initial alembic revision

Revision ID: d4bcebf28361
Revises: 
Create Date: 2023-09-25 23:19:10.708783

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4bcebf28361"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["category.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "asset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("details", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("cents", sa.Integer(), nullable=False),
        sa.Column("download_url", sa.String(), nullable=True),
        sa.Column("yanked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "download",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "illustration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("src", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tag_association_table",
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("tag_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["asset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tag.id"],
        ),
    )


def downgrade() -> None:
    op.drop_table("tag_association_table")
    op.drop_table("illustration")
    op.drop_table("download")
    op.drop_table("asset")
    op.drop_table("user")
    op.drop_table("tag")
    op.drop_table("category")

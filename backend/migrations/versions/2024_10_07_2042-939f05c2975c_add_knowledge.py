"""add knowledge

Revision ID: 939f05c2975c
Revises: 6a39f3d8e55c
Create Date: 2024-10-07 20:42:52.835698

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '939f05c2975c'
down_revision: Union[str, None] = 'c70e651b2e7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # Creating the 'knowledge' table
    from open_webui.utils.alembic import get_existing_tables

    tables = get_existing_tables(op
                                 )
    if "knowledge" not in tables:
        print("Creating knowledge table")
        op.create_table(
            "knowledge",
            sa.Column("id", sa.Text(), primary_key=True),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("data", sa.JSON(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
        )


def downgrade():
    op.drop_table("knowledge")

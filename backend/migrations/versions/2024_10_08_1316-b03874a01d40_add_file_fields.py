"""Add file fields

Revision ID: b03874a01d40
Revises: 939f05c2975c
Create Date: 2024-10-08 13:16:31.284407

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b03874a01d40"
down_revision: Union[str, None] = "939f05c2975c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("file", sa.Column("hash", sa.Text(), nullable=True))
    op.add_column("file", sa.Column("data", sa.JSON(), nullable=True))
    op.add_column(
        "file",
        sa.Column(
            "updated_at",
            sa.BigInteger(),
            nullable=True,
            server_default=sa.text("round(extract(epoch from now()))"),
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("file", "updated_at")
    op.drop_column("file", "data")
    op.drop_column("file", "hash")
    # ### end Alembic commands ###

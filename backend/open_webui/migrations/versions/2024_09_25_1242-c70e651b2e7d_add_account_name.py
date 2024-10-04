"""convert to jsonb

Revision ID: c70e651b2e7d
Revises: f622d7777d61
Create Date: 2024-09-25 12:42:46.202895

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.apps.webui.internal.db
from sqlalchemy.dialects.postgresql.json import JSONB


# revision identifiers, used by Alembic.
revision: str = "c70e651b2e7d"
down_revision: Union[str, None] = "f622d7777d61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "username_mapping",
        sa.Column("account_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    pass

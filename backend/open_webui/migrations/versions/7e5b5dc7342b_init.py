"""init

Revision ID: 7e5b5dc7342b
Revises:
Create Date: 2024-06-24 13:15:33.808998

"""

from typing import Sequence, Union

import open_webui.apps.webui.internal.db
import sqlalchemy as sa
from alembic import op
from open_webui.migrations.util import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = "7e5b5dc7342b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    # ### commands auto generated by Alembic - please adjust! ###
    if "auth" not in existing_tables:
        op.create_table(
            "auth",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("password", sa.Text(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "chat" not in existing_tables:
        op.create_table(
            "chat",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("chat", sa.Text(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("share_id", sa.Text(), nullable=True),
            sa.Column("archived", sa.Boolean(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("share_id"),
        )

    if "chatidtag" not in existing_tables:
        op.create_table(
            "chatidtag",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("tag_name", sa.String(), nullable=True),
            sa.Column("chat_id", sa.String(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "document" not in existing_tables:
        op.create_table(
            "document",
            sa.Column("collection_name", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("filename", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("collection_name"),
            sa.UniqueConstraint("name"),
        )

    if "file" not in existing_tables:
        op.create_table(
            "file",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("filename", sa.Text(), nullable=True),
            sa.Column(
                "meta", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "function" not in existing_tables:
        op.create_table(
            "function",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("type", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column(
                "meta", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "valves", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("is_global", sa.Boolean(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "memory" not in existing_tables:
        op.create_table(
            "memory",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "model" not in existing_tables:
        op.create_table(
            "model",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=True),
            sa.Column("base_model_id", sa.Text(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column(
                "params", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "meta", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "prompt" not in existing_tables:
        op.create_table(
            "prompt",
            sa.Column("command", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("command"),
        )

    if "tag" not in existing_tables:
        op.create_table(
            "tag",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("data", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "tool" not in existing_tables:
        op.create_table(
            "tool",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column(
                "specs", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "meta", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "valves", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "user" not in existing_tables:
        op.create_table(
            "user",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("profile_image_url", sa.Text(), nullable=True),
            sa.Column("last_active_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("api_key", sa.String(), nullable=True),
            sa.Column(
                "settings", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "info", open_webui.apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("oauth_sub", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key"),
            sa.UniqueConstraint("oauth_sub"),
        )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user")
    op.drop_table("tool")
    op.drop_table("tag")
    op.drop_table("prompt")
    op.drop_table("model")
    op.drop_table("memory")
    op.drop_table("function")
    op.drop_table("file")
    op.drop_table("document")
    op.drop_table("chatidtag")
    op.drop_table("chat")
    op.drop_table("auth")
    # ### end Alembic commands ###

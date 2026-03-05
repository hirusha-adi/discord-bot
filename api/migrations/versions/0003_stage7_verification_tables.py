"""stage7 verification tables

Revision ID: 0003_stage7_verification_tables
Revises: 0002_stage2_auth_columns
Create Date: 2026-03-06 04:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_stage7_verification_tables"
down_revision: Union[str, Sequence[str], None] = "0002_stage2_auth_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "verification_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("member_discord_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id", "member_discord_id", name="uq_verification_links_guild_member"),
    )
    op.create_index(op.f("ix_verification_links_id"), "verification_links", ["id"], unique=False)
    op.create_index(op.f("ix_verification_links_guild_id"), "verification_links", ["guild_id"], unique=False)
    op.create_index("ix_verification_links_guild_id_email", "verification_links", ["guild_id", "email"], unique=False)

    op.create_table(
        "verification_sync_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_member_discord_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_verification_sync_requests_id"), "verification_sync_requests", ["id"], unique=False)
    op.create_index(op.f("ix_verification_sync_requests_guild_id"), "verification_sync_requests", ["guild_id"], unique=False)
    op.create_index(
        "ix_verification_sync_requests_guild_id_status",
        "verification_sync_requests",
        ["guild_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_verification_sync_requests_guild_id_status", table_name="verification_sync_requests")
    op.drop_index(op.f("ix_verification_sync_requests_guild_id"), table_name="verification_sync_requests")
    op.drop_index(op.f("ix_verification_sync_requests_id"), table_name="verification_sync_requests")
    op.drop_table("verification_sync_requests")

    op.drop_index("ix_verification_links_guild_id_email", table_name="verification_links")
    op.drop_index(op.f("ix_verification_links_guild_id"), table_name="verification_links")
    op.drop_index(op.f("ix_verification_links_id"), table_name="verification_links")
    op.drop_table("verification_links")

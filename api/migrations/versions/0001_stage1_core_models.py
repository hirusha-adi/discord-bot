"""stage1 core models

Revision ID: 0001_stage1_core_models
Revises:
Create Date: 2026-03-06 01:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_stage1_core_models"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("discord_user_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discord_user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "guilds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("discord_guild_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bot_present", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discord_guild_id"),
    )
    op.create_index(op.f("ix_guilds_discord_guild_id"), "guilds", ["discord_guild_id"], unique=True)
    op.create_index(op.f("ix_guilds_id"), "guilds", ["id"], unique=False)

    op.create_table(
        "guild_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("discord_user_id", sa.String(length=64), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("can_manage_guild", sa.Boolean(), nullable=False),
        sa.Column("permission_bits", sa.String(length=64), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id", "user_id", name="uq_guild_users_guild_id_user_id"),
    )
    op.create_index(op.f("ix_guild_users_guild_id"), "guild_users", ["guild_id"], unique=False)
    op.create_index(op.f("ix_guild_users_id"), "guild_users", ["id"], unique=False)
    op.create_index(op.f("ix_guild_users_user_id"), "guild_users", ["user_id"], unique=False)

    op.create_table(
        "welcome_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("markdown_text", sa.Text(), nullable=True),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id"),
    )
    op.create_index(op.f("ix_welcome_configs_guild_id"), "welcome_configs", ["guild_id"], unique=True)
    op.create_index(op.f("ix_welcome_configs_id"), "welcome_configs", ["id"], unique=False)

    op.create_table(
        "leave_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("markdown_text", sa.Text(), nullable=True),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id"),
    )
    op.create_index(op.f("ix_leave_configs_guild_id"), "leave_configs", ["guild_id"], unique=True)
    op.create_index(op.f("ix_leave_configs_id"), "leave_configs", ["id"], unique=False)

    op.create_table(
        "verification_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("role_ids", sa.JSON(), nullable=True),
        sa.Column("remove_roles_when_unlisted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id"),
    )
    op.create_index(op.f("ix_verification_configs_guild_id"), "verification_configs", ["guild_id"], unique=True)
    op.create_index(op.f("ix_verification_configs_id"), "verification_configs", ["id"], unique=False)

    op.create_table(
        "registered_member_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_registered_member_lists_guild_id"), "registered_member_lists", ["guild_id"], unique=False)
    op.create_index(op.f("ix_registered_member_lists_id"), "registered_member_lists", ["id"], unique=False)

    op.create_table(
        "audit_log_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("destination_type", sa.String(length=32), nullable=False),
        sa.Column("log_channel_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id"),
    )
    op.create_index(op.f("ix_audit_log_configs_guild_id"), "audit_log_configs", ["guild_id"], unique=True)
    op.create_index(op.f("ix_audit_log_configs_id"), "audit_log_configs", ["id"], unique=False)

    op.create_table(
        "announcement_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("default_channel_id", sa.String(length=64), nullable=True),
        sa.Column("allowed_role_ids", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id"),
    )
    op.create_index(op.f("ix_announcement_configs_guild_id"), "announcement_configs", ["guild_id"], unique=True)
    op.create_index(op.f("ix_announcement_configs_id"), "announcement_configs", ["id"], unique=False)

    op.create_table(
        "registered_member_emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("member_list_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_list_id"], ["registered_member_lists.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guild_id", "email", name="uq_registered_member_emails_guild_id_email"),
    )
    op.create_index(op.f("ix_registered_member_emails_id"), "registered_member_emails", ["id"], unique=False)
    op.create_index("ix_registered_member_email_guild_id_email", "registered_member_emails", ["guild_id", "email"], unique=False)

    op.create_table(
        "message_audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.Column("author_discord_id", sa.String(length=64), nullable=True),
        sa.Column("channel_discord_id", sa.String(length=64), nullable=True),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("old_content", sa.Text(), nullable=True),
        sa.Column("new_content", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_message_audit_events_id"), "message_audit_events", ["id"], unique=False)
    op.create_index("ix_message_audit_event_guild_id_message_id", "message_audit_events", ["guild_id", "message_id"], unique=False)

    op.create_table(
        "scheduled_announcements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("image_urls", sa.JSON(), nullable=True),
        sa.Column("ping_everyone", sa.Boolean(), nullable=False),
        sa.Column("ping_role_ids", sa.JSON(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scheduled_announcements_id"), "scheduled_announcements", ["id"], unique=False)
    op.create_index(
        "ix_scheduled_announcement_guild_id_scheduled_at",
        "scheduled_announcements",
        ["guild_id", "scheduled_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scheduled_announcement_guild_id_scheduled_at", table_name="scheduled_announcements")
    op.drop_index(op.f("ix_scheduled_announcements_id"), table_name="scheduled_announcements")
    op.drop_table("scheduled_announcements")

    op.drop_index("ix_message_audit_event_guild_id_message_id", table_name="message_audit_events")
    op.drop_index(op.f("ix_message_audit_events_id"), table_name="message_audit_events")
    op.drop_table("message_audit_events")

    op.drop_index("ix_registered_member_email_guild_id_email", table_name="registered_member_emails")
    op.drop_index(op.f("ix_registered_member_emails_id"), table_name="registered_member_emails")
    op.drop_table("registered_member_emails")

    op.drop_index(op.f("ix_announcement_configs_id"), table_name="announcement_configs")
    op.drop_index(op.f("ix_announcement_configs_guild_id"), table_name="announcement_configs")
    op.drop_table("announcement_configs")

    op.drop_index(op.f("ix_audit_log_configs_id"), table_name="audit_log_configs")
    op.drop_index(op.f("ix_audit_log_configs_guild_id"), table_name="audit_log_configs")
    op.drop_table("audit_log_configs")

    op.drop_index(op.f("ix_registered_member_lists_id"), table_name="registered_member_lists")
    op.drop_index(op.f("ix_registered_member_lists_guild_id"), table_name="registered_member_lists")
    op.drop_table("registered_member_lists")

    op.drop_index(op.f("ix_verification_configs_id"), table_name="verification_configs")
    op.drop_index(op.f("ix_verification_configs_guild_id"), table_name="verification_configs")
    op.drop_table("verification_configs")

    op.drop_index(op.f("ix_leave_configs_id"), table_name="leave_configs")
    op.drop_index(op.f("ix_leave_configs_guild_id"), table_name="leave_configs")
    op.drop_table("leave_configs")

    op.drop_index(op.f("ix_welcome_configs_id"), table_name="welcome_configs")
    op.drop_index(op.f("ix_welcome_configs_guild_id"), table_name="welcome_configs")
    op.drop_table("welcome_configs")

    op.drop_index(op.f("ix_guild_users_user_id"), table_name="guild_users")
    op.drop_index(op.f("ix_guild_users_id"), table_name="guild_users")
    op.drop_index(op.f("ix_guild_users_guild_id"), table_name="guild_users")
    op.drop_table("guild_users")

    op.drop_index(op.f("ix_guilds_id"), table_name="guilds")
    op.drop_index(op.f("ix_guilds_discord_guild_id"), table_name="guilds")
    op.drop_table("guilds")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

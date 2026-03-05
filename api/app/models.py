from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discord_user_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discord_guild_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class GuildUser(Base):
    __tablename__ = "guild_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    discord_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_manage_guild: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permission_bits: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("guild_id", "user_id", name="uq_guild_users_guild_id_user_id"),)


class WelcomeConfig(Base):
    __tablename__ = "welcome_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(
        ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    markdown_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)


class LeaveConfig(Base):
    __tablename__ = "leave_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(
        ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    markdown_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)


class VerificationConfig(Base):
    __tablename__ = "verification_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(
        ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    remove_roles_when_unlisted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RegisteredMemberList(Base):
    __tablename__ = "registered_member_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="upload", nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RegisteredMemberEmail(Base):
    __tablename__ = "registered_member_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    member_list_id: Mapped[int | None] = mapped_column(
        ForeignKey("registered_member_lists.id", ondelete="SET NULL"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("guild_id", "email", name="uq_registered_member_emails_guild_id_email"),
        Index("ix_registered_member_email_guild_id_email", "guild_id", "email"),
    )


class AuditLogConfig(Base):
    __tablename__ = "audit_log_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(
        ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    destination_type: Mapped[str] = mapped_column(String(32), default="dashboard", nullable=False)
    log_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MessageAuditEvent(Base):
    __tablename__ = "message_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)
    author_discord_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_discord_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    old_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_message_audit_event_guild_id_message_id", "guild_id", "message_id"),)


class AnnouncementConfig(Base):
    __tablename__ = "announcement_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(
        ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    allowed_role_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ScheduledAnnouncement(Base):
    __tablename__ = "scheduled_announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    image_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ping_everyone: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ping_role_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_scheduled_announcement_guild_id_scheduled_at", "guild_id", "scheduled_at"),)

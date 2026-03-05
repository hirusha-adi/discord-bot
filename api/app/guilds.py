import os
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import (
    AnnouncementConfig,
    AuditLogConfig,
    Guild,
    GuildUser,
    LeaveConfig,
    User,
    VerificationConfig,
    WelcomeConfig,
)

router = APIRouter(prefix="/guilds", tags=["guilds"])

DISCORD_USER_GUILDS_URL = "https://discord.com/api/users/@me/guilds"
DISCORD_GUILD_URL_TEMPLATE = "https://discord.com/api/guilds/{guild_id}"

ADMINISTRATOR_PERMISSION = 0x8
MANAGE_GUILD_PERMISSION = 0x20


class GuildListItem(BaseModel):
    id: str
    name: str
    icon: str | None
    permissions: str


class ModuleOverviewItem(BaseModel):
    key: str
    enabled: bool


class GuildOverview(BaseModel):
    guild: GuildListItem
    stats: dict[str, str | int]
    modules: list[ModuleOverviewItem]


class AuthorizedGuild(BaseModel):
    id: str
    name: str
    icon: str | None
    permissions: str


def _has_manage_permission(permission_bits: str) -> bool:
    permissions = int(permission_bits)
    return bool(permissions & ADMINISTRATOR_PERMISSION or permissions & MANAGE_GUILD_PERMISSION)


def _bot_is_in_guild(client: httpx.Client, guild_id: str, bot_token: str) -> bool:
    # Primary Stage 3+ strategy: direct Discord API check per guild using bot token.
    response = client.get(
        DISCORD_GUILD_URL_TEMPLATE.format(guild_id=guild_id),
        headers={"Authorization": f"Bot {bot_token}"},
    )
    return response.status_code == 200


def _sync_guild_cache(db: Session, user: User, guilds: list[dict]) -> None:
    for guild_payload in guilds:
        discord_guild_id = guild_payload["id"]
        guild_row = db.execute(select(Guild).where(Guild.discord_guild_id == discord_guild_id)).scalar_one_or_none()
        if guild_row is None:
            guild_row = Guild(
                discord_guild_id=discord_guild_id,
                name=guild_payload["name"],
                bot_present=True,
            )
            db.add(guild_row)
            db.flush()
        else:
            guild_row.name = guild_payload["name"]
            guild_row.bot_present = True

        permissions = guild_payload["permissions"]
        guild_user = db.execute(
            select(GuildUser).where(GuildUser.guild_id == guild_row.id, GuildUser.user_id == user.id)
        ).scalar_one_or_none()

        if guild_user is None:
            guild_user = GuildUser(
                guild_id=guild_row.id,
                user_id=user.id,
                discord_user_id=user.discord_user_id or str(user.id),
            )
            db.add(guild_user)

        guild_user.permission_bits = permissions
        guild_user.is_admin = bool(int(permissions) & ADMINISTRATOR_PERMISSION)
        guild_user.can_manage_guild = bool(int(permissions) & MANAGE_GUILD_PERMISSION)
        guild_user.last_synced_at = datetime.now(UTC)

    db.commit()


def _fetch_manageable_guilds_live(user: User) -> list[dict]:
    if not user.discord_access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Discord login required")

    if user.discord_token_expires_at and user.discord_token_expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Discord session expired")

    bot_token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not bot_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DISCORD_BOT_TOKEN is not configured",
        )

    with httpx.Client(timeout=10.0) as client:
        user_guilds_response = client.get(
            DISCORD_USER_GUILDS_URL,
            headers={"Authorization": f"Bearer {user.discord_access_token}"},
        )

        if user_guilds_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to fetch Discord guilds for user",
            )

        user_guilds = user_guilds_response.json()

        filtered = []
        for guild in user_guilds:
            permissions = guild.get("permissions", "0")
            if not _has_manage_permission(permissions):
                continue

            guild_id = str(guild["id"])
            if not _bot_is_in_guild(client, guild_id, bot_token):
                continue

            filtered.append(
                {
                    "id": guild_id,
                    "name": guild.get("name", "Unknown Guild"),
                    "icon": guild.get("icon"),
                    "permissions": permissions,
                }
            )

        return filtered


def _fetch_manageable_guilds_from_cache(db: Session, user: User) -> list[dict]:
    stmt = (
        select(Guild, GuildUser)
        .join(GuildUser, GuildUser.guild_id == Guild.id)
        .where(
            GuildUser.user_id == user.id,
            Guild.bot_present.is_(True),
            (GuildUser.is_admin.is_(True) | GuildUser.can_manage_guild.is_(True)),
        )
    )
    rows = db.execute(stmt).all()

    return [
        {
            "id": row.Guild.discord_guild_id,
            "name": row.Guild.name,
            "icon": None,
            "permissions": row.GuildUser.permission_bits or "0",
        }
        for row in rows
    ]


def get_authorized_guilds(db: Session, user: User) -> list[AuthorizedGuild]:
    try:
        live = _fetch_manageable_guilds_live(user)
        _sync_guild_cache(db, user, live)
        return [AuthorizedGuild(**guild) for guild in live]
    except HTTPException as exc:
        # If Discord access is unavailable, fallback to previously synced cache.
        if exc.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_500_INTERNAL_SERVER_ERROR}:
            cached = _fetch_manageable_guilds_from_cache(db, user)
            if cached:
                return [AuthorizedGuild(**guild) for guild in cached]
        raise


def require_authorized_guild(db: Session, user: User, guild_id: str) -> AuthorizedGuild:
    guilds = get_authorized_guilds(db, user)
    selected = next((guild for guild in guilds if guild.id == guild_id), None)
    if selected is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guild not found or not authorized")
    return selected


def ensure_guild_row(db: Session, guild: AuthorizedGuild) -> Guild:
    guild_row = db.execute(select(Guild).where(Guild.discord_guild_id == guild.id)).scalar_one_or_none()
    if guild_row is None:
        guild_row = Guild(
            discord_guild_id=guild.id,
            name=guild.name,
            bot_present=True,
        )
        db.add(guild_row)
        db.commit()
        db.refresh(guild_row)
    return guild_row


def _build_modules_overview(db: Session, guild_row_id: int) -> list[ModuleOverviewItem]:
    welcome = db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == guild_row_id)).scalar_one_or_none()
    leave = db.execute(select(LeaveConfig).where(LeaveConfig.guild_id == guild_row_id)).scalar_one_or_none()
    verification = db.execute(select(VerificationConfig).where(VerificationConfig.guild_id == guild_row_id)).scalar_one_or_none()
    audit = db.execute(select(AuditLogConfig).where(AuditLogConfig.guild_id == guild_row_id)).scalar_one_or_none()
    announcements = db.execute(select(AnnouncementConfig).where(AnnouncementConfig.guild_id == guild_row_id)).scalar_one_or_none()

    return [
        ModuleOverviewItem(key="welcome_dm", enabled=bool(welcome and welcome.enabled)),
        ModuleOverviewItem(key="leave_dm", enabled=bool(leave and leave.enabled)),
        ModuleOverviewItem(key="verification", enabled=bool(verification and verification.enabled)),
        ModuleOverviewItem(key="audit_logging", enabled=bool(audit and audit.enabled)),
        ModuleOverviewItem(key="announcements", enabled=bool(announcements and announcements.enabled)),
    ]


@router.get("", response_model=list[GuildListItem])
def list_guilds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[GuildListItem]:
    guilds = get_authorized_guilds(db, current_user)
    return [GuildListItem(**guild.model_dump()) for guild in guilds]


@router.get("/{guild_id}/overview", response_model=GuildOverview)
def guild_overview(
    guild_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GuildOverview:
    authorized = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized)

    modules = _build_modules_overview(db, guild_row.id)
    stats = {
        "member_count": 0,
        "member_count_note": "TODO: member count will be provided in a later stage",
        "enabled_modules": sum(1 for module in modules if module.enabled),
        "total_modules": len(modules),
    }

    return GuildOverview(
        guild=GuildListItem(**authorized.model_dump()),
        stats=stats,
        modules=modules,
    )

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


def _require_discord_access_token(user: User) -> str:
    if not user.discord_access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Discord login required")

    if user.discord_token_expires_at and user.discord_token_expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Discord session expired")

    return user.discord_access_token


def _has_manage_permission(permission_bits: str) -> bool:
    permissions = int(permission_bits)
    return bool(permissions & ADMINISTRATOR_PERMISSION or permissions & MANAGE_GUILD_PERMISSION)


def _bot_is_in_guild(client: httpx.Client, guild_id: str, bot_token: str) -> bool:
    # Stage 3 approach: use Discord API per guild with the bot token.
    # 200 means bot can access guild metadata => bot is present in guild.
    response = client.get(
        DISCORD_GUILD_URL_TEMPLATE.format(guild_id=guild_id),
        headers={"Authorization": f"Bot {bot_token}"},
    )
    return response.status_code == 200


def _fetch_manageable_guilds_for_user(user: User) -> list[dict]:
    access_token = _require_discord_access_token(user)
    bot_token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not bot_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DISCORD_BOT_TOKEN is not configured")

    with httpx.Client(timeout=10.0) as client:
        user_guilds_response = client.get(
            DISCORD_USER_GUILDS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
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


def _build_modules_overview(db: Session, discord_guild_id: str) -> list[ModuleOverviewItem]:
    guild_row = db.execute(select(Guild).where(Guild.discord_guild_id == discord_guild_id)).scalar_one_or_none()
    if guild_row is None:
        return [
            ModuleOverviewItem(key="welcome_dm", enabled=False),
            ModuleOverviewItem(key="leave_dm", enabled=False),
            ModuleOverviewItem(key="verification", enabled=False),
            ModuleOverviewItem(key="audit_logging", enabled=False),
            ModuleOverviewItem(key="announcements", enabled=False),
        ]

    welcome = db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == guild_row.id)).scalar_one_or_none()
    leave = db.execute(select(LeaveConfig).where(LeaveConfig.guild_id == guild_row.id)).scalar_one_or_none()
    verification = db.execute(select(VerificationConfig).where(VerificationConfig.guild_id == guild_row.id)).scalar_one_or_none()
    audit = db.execute(select(AuditLogConfig).where(AuditLogConfig.guild_id == guild_row.id)).scalar_one_or_none()
    announcements = db.execute(select(AnnouncementConfig).where(AnnouncementConfig.guild_id == guild_row.id)).scalar_one_or_none()

    return [
        ModuleOverviewItem(key="welcome_dm", enabled=bool(welcome and welcome.enabled)),
        ModuleOverviewItem(key="leave_dm", enabled=bool(leave and leave.enabled)),
        ModuleOverviewItem(key="verification", enabled=bool(verification and verification.enabled)),
        ModuleOverviewItem(key="audit_logging", enabled=bool(audit and audit.enabled)),
        ModuleOverviewItem(key="announcements", enabled=bool(announcements and announcements.enabled)),
    ]


@router.get("", response_model=list[GuildListItem])
def list_guilds(current_user: User = Depends(get_current_user)) -> list[GuildListItem]:
    guilds = _fetch_manageable_guilds_for_user(current_user)
    return [GuildListItem(**guild) for guild in guilds]


@router.get("/{guild_id}/overview", response_model=GuildOverview)
def guild_overview(
    guild_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GuildOverview:
    guilds = _fetch_manageable_guilds_for_user(current_user)
    selected = next((guild for guild in guilds if guild["id"] == guild_id), None)
    if selected is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guild not found or not authorized")

    modules = _build_modules_overview(db, guild_id)
    stats = {
        "member_count": 0,
        "member_count_note": "TODO: member count will be provided in a later stage",
        "enabled_modules": sum(1 for module in modules if module.enabled),
        "total_modules": len(modules),
    }

    return GuildOverview(guild=GuildListItem(**selected), stats=stats, modules=modules)

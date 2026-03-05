import os
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnnouncementConfig, Guild, ScheduledAnnouncement

DISCORD_CHANNEL_MESSAGE_URL = "https://discord.com/api/v10/channels/{channel_id}/messages"


@dataclass
class AnnouncementRequest:
    guild_row_id: int
    content_markdown: str
    image_urls: list[str]
    mention_policy: str
    mention_role_ids: list[str]
    channel_discord_id: str | None


def _get_announcement_config(db: Session, guild_row_id: int) -> AnnouncementConfig | None:
    return db.execute(select(AnnouncementConfig).where(AnnouncementConfig.guild_id == guild_row_id)).scalar_one_or_none()


def resolve_channel_for_announcement(
    db: Session,
    guild_row_id: int,
    requested_channel_id: str | None,
) -> str:
    if requested_channel_id is not None and requested_channel_id.strip():
        return requested_channel_id.strip()

    config = _get_announcement_config(db, guild_row_id)
    if config and config.default_channel_id:
        return config.default_channel_id

    raise ValueError("No channel provided and no default announcement channel configured")


def ensure_announcement_module_enabled(db: Session, guild_row_id: int) -> None:
    config = _get_announcement_config(db, guild_row_id)
    if not config or not config.enabled:
        raise ValueError("Announcement module is disabled for this guild")


def _build_allowed_mentions(mention_policy: str, mention_role_ids: list[str]) -> dict:
    if mention_policy == "none":
        return {"parse": []}
    if mention_policy == "everyone":
        return {"parse": ["everyone"], "roles": [], "users": []}
    if mention_policy == "roles":
        cleaned_roles = [role_id for role_id in mention_role_ids if role_id.isdigit()]
        return {"parse": [], "roles": cleaned_roles, "users": []}
    raise ValueError("Invalid mention policy")


def _build_embeds(image_urls: list[str]) -> list[dict]:
    embeds = []
    for image_url in image_urls[:10]:
        if image_url:
            embeds.append({"image": {"url": image_url}})
    return embeds


def send_announcement_to_discord(request: AnnouncementRequest) -> tuple[bool, str | None]:
    bot_token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not bot_token or bot_token == "replace_me":
        return False, "DISCORD_BOT_TOKEN is not configured"

    if not request.channel_discord_id or not request.channel_discord_id.isdigit():
        return False, "Invalid channel id"

    payload = {
        "content": request.content_markdown,
        "embeds": _build_embeds(request.image_urls),
        "allowed_mentions": _build_allowed_mentions(request.mention_policy, request.mention_role_ids),
    }

    with httpx.Client(timeout=15.0) as client:
        response = client.post(
            DISCORD_CHANNEL_MESSAGE_URL.format(channel_id=request.channel_discord_id),
            headers={"Authorization": f"Bot {bot_token}"},
            json=payload,
        )

    if 200 <= response.status_code < 300:
        return True, None

    return False, f"Discord API error {response.status_code}: {response.text[:500]}"


def scheduled_announcement_to_request(db: Session, scheduled: ScheduledAnnouncement) -> AnnouncementRequest:
    guild_row = db.execute(select(Guild).where(Guild.id == scheduled.guild_id)).scalar_one()
    channel_id = scheduled.channel_discord_id
    if not channel_id:
        config = _get_announcement_config(db, guild_row.id)
        channel_id = config.default_channel_id if config else None

    mention_policy = "none"
    mention_roles = [str(role_id) for role_id in (scheduled.ping_role_ids or [])]
    if scheduled.ping_everyone:
        mention_policy = "everyone"
    elif mention_roles:
        mention_policy = "roles"

    return AnnouncementRequest(
        guild_row_id=guild_row.id,
        content_markdown=scheduled.content_markdown,
        image_urls=scheduled.image_urls or [],
        mention_policy=mention_policy,
        mention_role_ids=mention_roles,
        channel_discord_id=channel_id,
    )

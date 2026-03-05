from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.announcement_dispatch import (
    AnnouncementRequest,
    ensure_announcement_module_enabled,
    resolve_channel_for_announcement,
    send_announcement_to_discord,
)
from app.db import get_db
from app.deps import get_current_user
from app.guilds import ensure_guild_row, require_authorized_guild
from app.models import ScheduledAnnouncement, User

router = APIRouter(prefix="/guilds/{guild_id}/announcements", tags=["announcements"])


class AnnouncementBasePayload(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    channel_id: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    mention_policy: Literal["none", "roles", "everyone"] = "none"
    role_ids: list[str] = Field(default_factory=list)


class SendNowResponse(BaseModel):
    status: str
    channel_id: str


class SchedulePayload(AnnouncementBasePayload):
    scheduled_at: datetime


class ScheduledAnnouncementOut(BaseModel):
    id: int
    guild_id: str
    channel_id: str | None
    content: str
    image_urls: list[str]
    mention_policy: Literal["none", "roles", "everyone"]
    role_ids: list[str]
    scheduled_at: datetime
    status: str
    retry_count: int
    next_attempt_at: datetime | None
    sent_at: datetime | None
    error_message: str | None
    created_at: datetime


class ScheduledAnnouncementListResponse(BaseModel):
    items: list[ScheduledAnnouncementOut]
    total: int
    limit: int
    offset: int


class CancelResponse(BaseModel):
    status: str
    id: int


def _to_mention_fields(item: ScheduledAnnouncement) -> tuple[Literal["none", "roles", "everyone"], list[str]]:
    role_ids = [str(role_id) for role_id in (item.ping_role_ids or [])]
    if item.ping_everyone:
        return "everyone", role_ids
    if role_ids:
        return "roles", role_ids
    return "none", role_ids


def _to_output(item: ScheduledAnnouncement, guild_id: str) -> ScheduledAnnouncementOut:
    mention_policy, role_ids = _to_mention_fields(item)
    return ScheduledAnnouncementOut(
        id=item.id,
        guild_id=guild_id,
        channel_id=item.channel_discord_id,
        content=item.content_markdown,
        image_urls=item.image_urls or [],
        mention_policy=mention_policy,
        role_ids=role_ids,
        scheduled_at=item.scheduled_at,
        status=item.status,
        retry_count=item.retry_count or 0,
        next_attempt_at=item.next_attempt_at,
        sent_at=item.sent_at,
        error_message=item.failure_reason,
        created_at=item.created_at,
    )


def _normalize_scheduled_at(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.post("/send-now", response_model=SendNowResponse)
def send_now(
    guild_id: str,
    payload: AnnouncementBasePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SendNowResponse:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    try:
        ensure_announcement_module_enabled(db, guild_row.id)
        channel_id = resolve_channel_for_announcement(db, guild_row.id, payload.channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    request = AnnouncementRequest(
        guild_row_id=guild_row.id,
        content_markdown=payload.content,
        image_urls=payload.image_urls,
        mention_policy=payload.mention_policy,
        mention_role_ids=payload.role_ids,
        channel_discord_id=channel_id,
    )
    success, error = send_announcement_to_discord(request)
    if not success:
        raise HTTPException(status_code=502, detail=error or "Failed to send announcement")

    return SendNowResponse(status="sent", channel_id=channel_id)


@router.post("/scheduled", response_model=ScheduledAnnouncementOut)
def create_scheduled_announcement(
    guild_id: str,
    payload: SchedulePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledAnnouncementOut:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    try:
        ensure_announcement_module_enabled(db, guild_row.id)
        channel_id = resolve_channel_for_announcement(db, guild_row.id, payload.channel_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    scheduled = ScheduledAnnouncement(
        guild_id=guild_row.id,
        channel_discord_id=channel_id,
        content_markdown=payload.content,
        image_urls=payload.image_urls,
        ping_everyone=payload.mention_policy == "everyone",
        ping_role_ids=payload.role_ids if payload.mention_policy == "roles" else [],
        scheduled_at=_normalize_scheduled_at(payload.scheduled_at),
        status="pending",
        retry_count=0,
        next_attempt_at=None,
        sent_at=None,
        failure_reason=None,
        created_at=datetime.now(UTC),
    )
    db.add(scheduled)
    db.commit()
    db.refresh(scheduled)
    return _to_output(scheduled, guild_id)


@router.get("/scheduled", response_model=ScheduledAnnouncementListResponse)
def list_scheduled_announcements(
    guild_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledAnnouncementListResponse:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    query = select(ScheduledAnnouncement).where(ScheduledAnnouncement.guild_id == guild_row.id)
    if status_filter:
        query = query.where(ScheduledAnnouncement.status == status_filter)

    items = (
        db.execute(query.order_by(ScheduledAnnouncement.scheduled_at.desc()).limit(limit).offset(offset)).scalars().all()
    )
    count_query = select(func.count()).select_from(query.subquery())
    total = int(db.execute(count_query).scalar_one())

    return ScheduledAnnouncementListResponse(
        items=[_to_output(item, guild_id) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/scheduled/{announcement_id}", response_model=ScheduledAnnouncementOut)
def get_scheduled_announcement(
    guild_id: str,
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledAnnouncementOut:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    item = db.execute(
        select(ScheduledAnnouncement).where(
            ScheduledAnnouncement.guild_id == guild_row.id,
            ScheduledAnnouncement.id == announcement_id,
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Scheduled announcement not found")

    return _to_output(item, guild_id)


@router.patch("/scheduled/{announcement_id}/cancel", response_model=CancelResponse)
def cancel_scheduled_announcement(
    guild_id: str,
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CancelResponse:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    item = db.execute(
        select(ScheduledAnnouncement).where(
            ScheduledAnnouncement.guild_id == guild_row.id,
            ScheduledAnnouncement.id == announcement_id,
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Scheduled announcement not found")

    if item.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending announcements can be cancelled")

    item.status = "cancelled"
    db.commit()
    return CancelResponse(status="cancelled", id=item.id)

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.guilds import ensure_guild_row, require_authorized_guild
from app.models import MessageAuditEvent, User

router = APIRouter(prefix="/guilds/{guild_id}/audit-logs", tags=["audit-logs"])


class MessageAuditEventOut(BaseModel):
    id: int
    event_type: str
    author_discord_id: str | None
    channel_discord_id: str | None
    message_id: str
    old_content: str | None
    new_content: str | None
    occurred_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[MessageAuditEventOut]
    total: int
    limit: int
    offset: int


def _apply_filters(
    stmt: Select[tuple[MessageAuditEvent]],
    guild_row_id: int,
    event_type: Literal["edit", "delete"] | None,
    channel_id: str | None,
    author_id: str | None,
    occurred_from: datetime | None,
    occurred_to: datetime | None,
) -> Select[tuple[MessageAuditEvent]]:
    stmt = stmt.where(MessageAuditEvent.guild_id == guild_row_id)

    if event_type is not None:
        stmt = stmt.where(MessageAuditEvent.event_type == event_type)
    if channel_id is not None:
        stmt = stmt.where(MessageAuditEvent.channel_discord_id == channel_id)
    if author_id is not None:
        stmt = stmt.where(MessageAuditEvent.author_discord_id == author_id)
    if occurred_from is not None:
        stmt = stmt.where(MessageAuditEvent.occurred_at >= occurred_from)
    if occurred_to is not None:
        stmt = stmt.where(MessageAuditEvent.occurred_at <= occurred_to)

    return stmt


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    guild_id: str,
    event_type: Literal["edit", "delete"] | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    author_id: str | None = Query(default=None),
    occurred_from: datetime | None = Query(default=None),
    occurred_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    base_stmt = select(MessageAuditEvent)
    filtered_stmt = _apply_filters(
        stmt=base_stmt,
        guild_row_id=guild_row.id,
        event_type=event_type,
        channel_id=channel_id,
        author_id=author_id,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )

    count_stmt = _apply_filters(
        stmt=select(MessageAuditEvent.id),
        guild_row_id=guild_row.id,
        event_type=event_type,
        channel_id=channel_id,
        author_id=author_id,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )

    items = (
        db.execute(
            filtered_stmt.order_by(MessageAuditEvent.occurred_at.desc(), MessageAuditEvent.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    total = db.execute(select(func.count()).select_from(count_stmt.subquery())).scalar_one()

    return AuditLogListResponse(
        items=[
            MessageAuditEventOut(
                id=item.id,
                event_type=item.event_type,
                author_discord_id=item.author_discord_id,
                channel_discord_id=item.channel_discord_id,
                message_id=item.message_id,
                old_content=item.old_content,
                new_content=item.new_content,
                occurred_at=item.occurred_at,
            )
            for item in items
        ],
        total=int(total),
        limit=limit,
        offset=offset,
    )

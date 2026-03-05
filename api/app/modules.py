from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.guilds import ensure_guild_row, require_authorized_guild
from app.models import (
    AnnouncementConfig,
    AuditLogConfig,
    LeaveConfig,
    User,
    VerificationConfig,
    WelcomeConfig,
)

router = APIRouter(prefix="/guilds/{guild_id}/modules", tags=["modules"])

MODULE_KEYS = {"welcome", "leave", "verification", "audit", "announcement"}


class TogglePayload(BaseModel):
    enabled: bool


class WelcomeUpdatePayload(BaseModel):
    enabled: bool | None = None
    markdown_text: str | None = None
    image_urls: list[str] | None = None


class LeaveUpdatePayload(BaseModel):
    enabled: bool | None = None
    markdown_text: str | None = None
    image_urls: list[str] | None = None


class VerificationUpdatePayload(BaseModel):
    enabled: bool | None = None
    role_ids: list[str] | None = None


class AuditUpdatePayload(BaseModel):
    enabled: bool | None = None
    destination_type: str | None = Field(default=None, pattern="^(dashboard|channel)$")
    log_channel_id: str | None = None


class AnnouncementUpdatePayload(BaseModel):
    enabled: bool | None = None
    default_channel_id: str | None = None


class ModuleConfigResponse(BaseModel):
    module: str
    guild_id: str
    enabled: bool
    config: dict[str, Any]


def _assert_module_key(module: str) -> None:
    if module not in MODULE_KEYS:
        raise HTTPException(status_code=404, detail="Module not found")


def _get_or_create_welcome(db: Session, guild_row_id: int) -> WelcomeConfig:
    row = db.execute(select(WelcomeConfig).where(WelcomeConfig.guild_id == guild_row_id)).scalar_one_or_none()
    if row is None:
        row = WelcomeConfig(guild_id=guild_row_id, enabled=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _get_or_create_leave(db: Session, guild_row_id: int) -> LeaveConfig:
    row = db.execute(select(LeaveConfig).where(LeaveConfig.guild_id == guild_row_id)).scalar_one_or_none()
    if row is None:
        row = LeaveConfig(guild_id=guild_row_id, enabled=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _get_or_create_verification(db: Session, guild_row_id: int) -> VerificationConfig:
    row = db.execute(select(VerificationConfig).where(VerificationConfig.guild_id == guild_row_id)).scalar_one_or_none()
    if row is None:
        row = VerificationConfig(guild_id=guild_row_id, enabled=False, role_ids=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _get_or_create_audit(db: Session, guild_row_id: int) -> AuditLogConfig:
    row = db.execute(select(AuditLogConfig).where(AuditLogConfig.guild_id == guild_row_id)).scalar_one_or_none()
    if row is None:
        row = AuditLogConfig(guild_id=guild_row_id, enabled=False, destination_type="dashboard")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _get_or_create_announcement(db: Session, guild_row_id: int) -> AnnouncementConfig:
    row = db.execute(select(AnnouncementConfig).where(AnnouncementConfig.guild_id == guild_row_id)).scalar_one_or_none()
    if row is None:
        row = AnnouncementConfig(guild_id=guild_row_id, enabled=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _response_for_module(module: str, guild_id: str, row: Any) -> ModuleConfigResponse:
    if module in {"welcome", "leave"}:
        return ModuleConfigResponse(
            module=module,
            guild_id=guild_id,
            enabled=row.enabled,
            config={
                "markdown_text": row.markdown_text,
                "image_urls": row.image_urls or [],
            },
        )

    if module == "verification":
        return ModuleConfigResponse(
            module=module,
            guild_id=guild_id,
            enabled=row.enabled,
            config={"role_ids": row.role_ids or []},
        )

    if module == "audit":
        return ModuleConfigResponse(
            module=module,
            guild_id=guild_id,
            enabled=row.enabled,
            config={
                "destination_type": row.destination_type,
                "log_channel_id": row.log_channel_id,
            },
        )

    return ModuleConfigResponse(
        module=module,
        guild_id=guild_id,
        enabled=row.enabled,
        config={"default_channel_id": row.default_channel_id},
    )


def _fetch_module_row(db: Session, module: str, guild_row_id: int) -> Any:
    if module == "welcome":
        return _get_or_create_welcome(db, guild_row_id)
    if module == "leave":
        return _get_or_create_leave(db, guild_row_id)
    if module == "verification":
        return _get_or_create_verification(db, guild_row_id)
    if module == "audit":
        return _get_or_create_audit(db, guild_row_id)
    return _get_or_create_announcement(db, guild_row_id)


@router.get("/{module}", response_model=ModuleConfigResponse)
def get_module_config(
    guild_id: str,
    module: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModuleConfigResponse:
    _assert_module_key(module)
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)
    row = _fetch_module_row(db, module, guild_row.id)
    return _response_for_module(module, guild_id, row)


@router.patch("/{module}/toggle", response_model=ModuleConfigResponse)
def toggle_module(
    guild_id: str,
    module: str,
    payload: TogglePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModuleConfigResponse:
    _assert_module_key(module)
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)
    row = _fetch_module_row(db, module, guild_row.id)
    row.enabled = payload.enabled
    db.commit()
    db.refresh(row)
    return _response_for_module(module, guild_id, row)


@router.put("/{module}", response_model=ModuleConfigResponse)
def update_module_config(
    guild_id: str,
    module: str,
    payload: dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModuleConfigResponse:
    _assert_module_key(module)
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    if module == "welcome":
        parsed = WelcomeUpdatePayload.model_validate(payload)
        row = _get_or_create_welcome(db, guild_row.id)
        if parsed.enabled is not None:
            row.enabled = parsed.enabled
        if parsed.markdown_text is not None:
            row.markdown_text = parsed.markdown_text
        if parsed.image_urls is not None:
            row.image_urls = parsed.image_urls

    elif module == "leave":
        parsed = LeaveUpdatePayload.model_validate(payload)
        row = _get_or_create_leave(db, guild_row.id)
        if parsed.enabled is not None:
            row.enabled = parsed.enabled
        if parsed.markdown_text is not None:
            row.markdown_text = parsed.markdown_text
        if parsed.image_urls is not None:
            row.image_urls = parsed.image_urls

    elif module == "verification":
        parsed = VerificationUpdatePayload.model_validate(payload)
        row = _get_or_create_verification(db, guild_row.id)
        if parsed.enabled is not None:
            row.enabled = parsed.enabled
        if parsed.role_ids is not None:
            row.role_ids = parsed.role_ids

    elif module == "audit":
        parsed = AuditUpdatePayload.model_validate(payload)
        row = _get_or_create_audit(db, guild_row.id)
        if parsed.enabled is not None:
            row.enabled = parsed.enabled
        if parsed.destination_type is not None:
            row.destination_type = parsed.destination_type
        if parsed.log_channel_id is not None:
            row.log_channel_id = parsed.log_channel_id

    else:
        parsed = AnnouncementUpdatePayload.model_validate(payload)
        row = _get_or_create_announcement(db, guild_row.id)
        if parsed.enabled is not None:
            row.enabled = parsed.enabled
        if parsed.default_channel_id is not None:
            row.default_channel_id = parsed.default_channel_id

    db.commit()
    db.refresh(row)
    return _response_for_module(module, guild_id, row)

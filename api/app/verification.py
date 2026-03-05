import hashlib
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.guilds import ensure_guild_row, require_authorized_guild
from app.models import (
    RegisteredMemberEmail,
    RegisteredMemberList,
    User,
    VerificationConfig,
    VerificationSyncRequest,
)

router = APIRouter(prefix="/guilds/{guild_id}/verification", tags=["verification"])

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


class VerificationUploadResponse(BaseModel):
    status: str
    imported_count: int
    sync_request_id: int


class VerificationSyncTriggerResponse(BaseModel):
    status: str
    sync_request_id: int


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _parse_emails(text_data: str) -> list[str]:
    emails: set[str] = set()
    for raw_line in text_data.splitlines():
        candidate = _normalize_email(raw_line)
        if not candidate:
            continue
        if EMAIL_PATTERN.match(candidate):
            emails.add(candidate)

    return sorted(emails)


def _get_or_create_verification_config(db: Session, guild_row_id: int) -> VerificationConfig:
    row = db.execute(select(VerificationConfig).where(VerificationConfig.guild_id == guild_row_id)).scalar_one_or_none()
    if row is None:
        row = VerificationConfig(guild_id=guild_row_id, enabled=False, role_ids=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _create_sync_request(
    db: Session,
    guild_row_id: int,
    source: str,
    requested_by_user_id: int | None,
) -> VerificationSyncRequest:
    request = VerificationSyncRequest(
        guild_id=guild_row_id,
        requested_by_user_id=requested_by_user_id,
        source=source,
        status="pending",
        requested_at=datetime.now(UTC),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.post("/members/upload", response_model=VerificationUploadResponse)
async def upload_members_list(
    guild_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerificationUploadResponse:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    verification_config = _get_or_create_verification_config(db, guild_row.id)
    if not verification_config.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification module is disabled")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    decoded_text = content.decode("utf-8", errors="ignore")
    emails = _parse_emails(decoded_text)
    if not emails:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid emails found in file")

    file_hash = hashlib.sha256(content).hexdigest()

    member_list = RegisteredMemberList(
        guild_id=guild_row.id,
        source_type="dashboard_upload",
        filename=file.filename,
        file_hash=file_hash,
        uploaded_at=datetime.now(UTC),
    )
    db.add(member_list)
    db.commit()
    db.refresh(member_list)

    # Consistent replacement strategy: member list upload fully refreshes registered emails for the guild.
    db.execute(delete(RegisteredMemberEmail).where(RegisteredMemberEmail.guild_id == guild_row.id))
    db.commit()

    for email in emails:
        db.add(
            RegisteredMemberEmail(
                guild_id=guild_row.id,
                member_list_id=member_list.id,
                email=email,
                created_at=datetime.now(UTC),
            )
        )
    db.commit()

    sync_request = _create_sync_request(
        db=db,
        guild_row_id=guild_row.id,
        source="dashboard_upload",
        requested_by_user_id=current_user.id,
    )

    return VerificationUploadResponse(
        status="ok",
        imported_count=len(emails),
        sync_request_id=sync_request.id,
    )


@router.post("/sync", response_model=VerificationSyncTriggerResponse)
def trigger_verification_sync(
    guild_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerificationSyncTriggerResponse:
    authorized_guild = require_authorized_guild(db, current_user, guild_id)
    guild_row = ensure_guild_row(db, authorized_guild)

    verification_config = _get_or_create_verification_config(db, guild_row.id)
    if not verification_config.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification module is disabled")

    sync_request = _create_sync_request(
        db=db,
        guild_row_id=guild_row.id,
        source="dashboard_manual_sync",
        requested_by_user_id=current_user.id,
    )

    return VerificationSyncTriggerResponse(status="ok", sync_request_id=sync_request.id)

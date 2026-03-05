from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import SESSION_COOKIE_NAME, decode_session_token


def get_current_user(
    db: Session = Depends(get_db), session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME)
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_session_token(session_token)
        user_id = int(payload["sub"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    stmt = select(User).where(or_(User.username == identifier, User.email == identifier))
    return db.execute(stmt).scalar_one_or_none()

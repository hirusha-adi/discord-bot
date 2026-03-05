import os
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, get_user_by_identifier
from app.models import User
from app.security import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DISCORD_OAUTH_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
DISCORD_OAUTH_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_ME_URL = "https://discord.com/api/users/@me"


class LocalAuthPayload(BaseModel):
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class AuthUserResponse(BaseModel):
    id: int
    username: str | None
    email: str | None
    discord_user_id: str | None


class AuthResponse(BaseModel):
    status: str
    user: AuthUserResponse


def _discord_client_id() -> str:
    value = os.getenv("DISCORD_CLIENT_ID", "")
    if not value:
        raise HTTPException(status_code=500, detail="DISCORD_CLIENT_ID is not configured")
    return value


def _discord_client_secret() -> str:
    value = os.getenv("DISCORD_CLIENT_SECRET", "")
    if not value:
        raise HTTPException(status_code=500, detail="DISCORD_CLIENT_SECRET is not configured")
    return value


def _discord_redirect_uri() -> str:
    value = os.getenv("DISCORD_REDIRECT_URI", "")
    if not value:
        raise HTTPException(status_code=500, detail="DISCORD_REDIRECT_URI is not configured")
    return value


def _discord_scope() -> str:
    return os.getenv("DISCORD_OAUTH_SCOPES", "identify guilds")


def _web_redirect_url() -> str:
    return os.getenv("WEB_LOGIN_REDIRECT_URL", "http://localhost:3000")


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = create_session_token(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=SESSION_MAX_AGE_SECONDS,
    )


def _user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(id=user.id, username=user.username, email=user.email, discord_user_id=user.discord_user_id)


@router.post("/local/register", response_model=AuthResponse)
def register_local(payload: LocalAuthPayload, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    existing = get_user_by_identifier(db, payload.identifier)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identifier already exists")

    is_email = "@" in payload.identifier
    user = User(
        username=None if is_email else payload.identifier,
        email=payload.identifier if is_email else None,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_session_cookie(response, user.id)
    return AuthResponse(status="ok", user=_user_response(user))


@router.post("/local/login", response_model=AuthResponse)
def login_local(payload: LocalAuthPayload, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_user_by_identifier(db, payload.identifier)
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    _set_session_cookie(response, user.id)
    return AuthResponse(status="ok", user=_user_response(user))


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"status": "ok"}


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(status="ok", user=_user_response(current_user))


@router.get("/discord/login")
def discord_login() -> Response:
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": _discord_client_id(),
        "redirect_uri": _discord_redirect_uri(),
        "response_type": "code",
        "scope": _discord_scope(),
        "state": state,
        "prompt": "consent",
    }
    authorize_url = f"{DISCORD_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    response = RedirectResponse(url=authorize_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        key="discord_oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
    )
    return response


@router.get("/discord/callback")
def discord_callback(
    code: str = Query(..., min_length=1),
    state: str = Query(..., min_length=1),
    oauth_state_cookie: str | None = Cookie(default=None, alias="discord_oauth_state"),
    db: Session = Depends(get_db),
) -> Response:
    if not oauth_state_cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing oauth state")

    if state != oauth_state_cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid oauth state")

    token_payload = {
        "client_id": _discord_client_id(),
        "client_secret": _discord_client_secret(),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": _discord_redirect_uri(),
    }

    with httpx.Client(timeout=10.0) as client:
        token_resp = client.post(
            DISCORD_OAUTH_TOKEN_URL,
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord token exchange failed")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Discord access token missing")

        me_resp = client.get(DISCORD_API_ME_URL, headers={"Authorization": f"Bearer {access_token}"})
        if me_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord user fetch failed")

        discord_user = me_resp.json()

    discord_user_id = str(discord_user["id"])
    username = discord_user.get("username")

    user = db.query(User).filter(User.discord_user_id == discord_user_id).first()
    if not user:
        user = User(username=username, discord_user_id=discord_user_id)
        db.add(user)

    expires_in = int(token_data.get("expires_in", 3600))
    user.discord_access_token = access_token
    user.discord_token_scope = token_data.get("scope")
    user.discord_token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    db.commit()
    db.refresh(user)

    redirect_response = RedirectResponse(url=_web_redirect_url(), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    _set_session_cookie(redirect_response, user.id)
    redirect_response.delete_cookie("discord_oauth_state")
    return redirect_response

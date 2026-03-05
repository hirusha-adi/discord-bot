import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.db import db_ping
from app.deps import get_current_user
from app.guilds import router as guilds_router
from app.models import User
from app.modules import router as modules_router

app = FastAPI(title="Discord Bot API", version="0.5.0")

web_origin = os.getenv("WEB_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(guilds_router)
app.include_router(modules_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/db/ping")
def ping_database() -> dict[str, str]:
    db_ping()
    return {"status": "ok", "service": "api", "database": "ok"}


@app.get("/protected/ping")
def protected_ping(current_user: User = Depends(get_current_user)) -> dict[str, str | int]:
    return {"status": "ok", "service": "api", "user_id": current_user.id}

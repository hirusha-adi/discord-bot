from fastapi import FastAPI

from app.db import db_ping

app = FastAPI(title="Discord Bot API", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/db/ping")
def ping_database() -> dict[str, str]:
    db_ping()
    return {"status": "ok", "service": "api", "database": "ok"}

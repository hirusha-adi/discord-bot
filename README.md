# Discord Bot Platform

Discord bot platform with:
- `bot` (`discord.py`)
- `api` (`FastAPI` + SQLAlchemy + Alembic)
- `web` (Next.js, JavaScript-only)
- `worker` (scheduled announcements dispatcher)

SQLite is the current runtime DB, persisted in Docker volumes, with a documented path to Postgres later.

## Local Development

### Prerequisites

- Docker Engine
- Docker Compose plugin (`docker compose`)

### Start stack

```bash
docker compose up --build
```

Services:
- API: `http://localhost:8000`
- Web: `http://localhost:3000`
- Bot: long-running process
- Worker: scheduled announcement dispatcher

### Verify

```bash
docker compose exec -T api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"
docker compose exec -T api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/db/ping').read().decode())"
docker compose logs -f api web bot worker
```

## Production Deployment (Single VPS)

### 1) Prepare environment

Create `.env` in repo root (do not commit it). Use `.env.example` as a template.

### 2) One-command deployment

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env up -d --build
```

This brings up `api`, `web`, `bot`, and `worker` with:
- persistent DB volume (`app_data`)
- restart policies
- API/Web healthchecks
- migration-on-start for API (`alembic upgrade head`)

### 3) Operational checks

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env ps
docker compose -f infra/docker-compose.prod.yml --env-file .env logs -f api web bot worker
```

## Logging and Reliability Notes

### Structured logging

Python services (`api`, `bot`, `worker`) use consistent log format:
- `ts=<timestamp> level=<LEVEL> service=<name> logger=<logger> msg=<message>`
- level controlled by `LOG_LEVEL` env var.

### Worker retries/backoff

Scheduled announcements now use capped retries:
- `ANNOUNCEMENT_WORKER_MAX_RETRIES` (default `3`)
- `ANNOUNCEMENT_WORKER_BACKOFF_SECONDS` (default `15`)
- exponential backoff (`base * 2^(retry-1)`)
- failed jobs persist `status=failed` + `failure_reason`.

### Discord rate-limit guards

Announcement send path includes basic guardrails:
- capped send retries (`DISCORD_POST_MAX_RETRIES`, default `3`)
- exponential backoff (`DISCORD_POST_BASE_BACKOFF_SECONDS`, default `2`)
- explicit `429` handling using Discord `retry_after` when present.

## SQLite Persistence, Backup, Restore

### Volume strategy

- SQLite file path inside containers: `/data/app.db`
- prod named volume: `app_data`
- Docker host location (typical): `/var/lib/docker/volumes/<project>_app_data/_data`

### Backup (recommended: stopped stack snapshot)

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env down
docker run --rm -v discord-bot_app_data:/data -v "$(pwd)/backups:/backup" alpine sh -c "cp /data/app.db /backup/app-$(date +%Y%m%d-%H%M%S).db"
docker compose -f infra/docker-compose.prod.yml --env-file .env up -d
```

### Backup (online SQLite backup via Python)

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env exec -T api python - <<'PY'
import sqlite3
src = sqlite3.connect('/data/app.db')
dst = sqlite3.connect('/data/app.backup.db')
src.backup(dst)
dst.close()
src.close()
print('backup complete: /data/app.backup.db')
PY
```

### Restore

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env down
docker run --rm -v discord-bot_app_data:/data -v "$(pwd)/backups:/backup" alpine sh -c "cp /backup/<backup-file>.db /data/app.db"
docker compose -f infra/docker-compose.prod.yml --env-file .env up -d --build
```

### Postgres migration note (high level)

Planned path:
1. Move `DATABASE_URL` to Postgres in `.env`.
2. Run Alembic migrations against Postgres.
3. Switch production compose from SQLite volume dependency to managed Postgres storage/backups.

## Security Review Checklist

- [ ] Keep secrets only in `.env`/secret manager. Never commit `.env`.
- [ ] Use strong `JWT_SECRET`; rotate if leaked.
- [ ] Ensure Discord OAuth redirect URI exactly matches app config.
- [ ] Keep OAuth scopes least-privilege (`identify guilds` for dashboard flows).
- [ ] Keep announcement mention policy explicit; default should remain `none`.
- [ ] Validate `allowed_mentions` use for every posting path.
- [ ] Review cookie/session settings (`httponly`, `samesite`, `secure` in production TLS deployments).
- [ ] Keep password hashing settings and dependencies current.
- [ ] Run dependency audits/updates regularly (`pip`, `npm`, base images).
- [ ] Redact tokens/secrets from logs; do not log Discord tokens or OAuth secrets.

## Useful Commands

```bash
# Dev
docker compose up --build
docker compose logs -f api web bot worker

# Prod
docker compose -f infra/docker-compose.prod.yml --env-file .env up -d --build
docker compose -f infra/docker-compose.prod.yml --env-file .env logs -f api web bot worker
docker compose -f infra/docker-compose.prod.yml --env-file .env down
```

# Discord Bot Platform (Stage 0)

## Prerequisites

- Docker Engine
- Docker Compose plugin (`docker compose`)

## Start development stack

```bash
docker compose up --build
```

This starts:
- `api` on `http://localhost:8000`
- `web` on `http://localhost:3000`
- `bot` as a placeholder long-running service

## Verify services

### API health

```bash
curl http://localhost:8000/health
```

Expected: HTTP 200 with JSON response.

### Web page

Open:

- `http://localhost:3000`

## Service logs

```bash
docker compose logs -f api
docker compose logs -f web
docker compose logs -f bot
```

## Production template

A production compose template is available at:

- `infra/docker-compose.prod.yml`

It is intentionally minimal for Stage 0 and will be completed in later stages.

# Discord Bot SaaS Platform

Production-oriented, multi-tenant Discord bot platform (MEE6-style) with:
- Discord bot service
- REST API backend
- Web dashboard
- Worker/queue processing
- Per-guild module configuration
- SQLite-first ORM design with PostgreSQL migration path

## Architecture
- Full system design: `docs/architecture/system-design.md`
- Repository layout: `docs/architecture/folder-structure.md`
- Phase 1 setup and validation: `docs/runbooks/phase1-setup.md`
- Full stack setup: `docs/runbooks/full-stack-setup.md`

## Workspace Structure
- `apps/bot`: Discord gateway service and module runtime.
- `apps/api`: Dashboard/backend REST API and worker entrypoints.
- `apps/web`: Admin dashboard frontend.
- `packages/*`: Shared DB, contracts, plugin SDK, security, queue, cache, and logging.
- `infra/*`: Docker, nginx, redis, monitoring, and IaC assets.
- `docs/*`: Architecture, APIs, module docs, and runbooks.
- `scripts/*`: Development, deployment, migration, and ops scripts.
- `tests/*`: Integration, E2E, and load testing.

## Current Status
Implementation baseline is in place across all services:
- `apps/bot`: command framework, module registry, slash + prefix handlers, and required Discord event handlers.
- `apps/api`: auth/session endpoints, guild/settings/modules APIs, analytics summary, owner admin metrics.
- `apps/web`: login, guild selection, and guild dashboard pages.
- `apps/api/src/workers`: scheduled task worker loop.
- `docker-compose.yml` + Dockerfiles for local orchestration.

## Quick Start
1. Copy env file: `Copy-Item .env.example .env`
2. Install deps: `pnpm install`
3. Prisma setup: `pnpm db:generate && pnpm db:migrate`
4. Register slash commands: `pnpm --filter @platform/bot register:commands`
5. Run services:
- `pnpm dev:api`
- `pnpm dev:bot`
- `pnpm dev:web`
- `pnpm dev:worker`
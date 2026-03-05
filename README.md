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
Phase 1 is implemented:
- Prisma schema and initial migration are added.
- Bot command `/create-dashboard-admin` is implemented with secure DM credential flow.
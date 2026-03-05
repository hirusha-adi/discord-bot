# Repository Folder Structure

## Monorepo Layout
```text
discord-bot/
  .github/
    agents/
      discord-saas-architect.agent.md
    workflows/
  apps/
    bot/
      src/
        adapters/
        commands/
          prefix/
          slash/
        core/
        events/
        jobs/
        modules/
          automation/
          economy/
          giveaways/
          leveling/
          logging/
          moderation/
          reaction-roles/
          tickets/
        sharding/
    api/
      src/
        middleware/
        modules/
          admin/
          analytics/
          auth/
          guilds/
          settings/
        plugins/
        workers/
    web/
      src/
        app/
          (auth)/
          (dashboard)/
        components/
          dashboard/
          modules/
        hooks/
        lib/
        styles/
  packages/
    cache/
    config/
    contracts/
    db/
      prisma/
      seeds/
    logger/
    plugin-sdk/
    queue/
    security/
    testing/
  infra/
    docker/
    monitoring/
    nginx/
    redis/
    terraform/
  docs/
    api/
    architecture/
      folder-structure.md
      system-design.md
    modules/
    runbooks/
  scripts/
    deploy/
    dev/
    migrations/
    ops/
  tests/
    e2e/
    integration/
    load/
  tools/
    generators/
  .changeset/
  README.md
```

## Ownership and Purpose
- `apps/bot`: Discord gateway and module runtime.
- `apps/api`: Authenticated REST API for dashboard and owner admin panel.
- `apps/web`: Next.js dashboard for guild admins.
- `packages/db`: ORM schema, migrations, seed data, and data helpers.
- `packages/plugin-sdk`: Contracts and helpers for module/plugin development.
- `packages/contracts`: Shared DTOs, event contracts, and validation schemas.
- `packages/security`: Auth/session primitives, permission guards, and rate-limit utilities.
- `packages/queue`: Queue producer/consumer abstractions.
- `packages/cache`: Redis cache helpers and key strategy.
- `infra/*`: Deployment and runtime infrastructure assets.
- `docs/*`: Architecture, runbooks, module docs, and API references.
- `scripts/*`: Local development, migration, deployment, and operations scripts.
- `tests/*`: Cross-service test suites.
- `tools/generators`: Scaffolding for new modules/commands/routes.

## Service Boundaries
- Bot never talks directly to dashboard frontend.
- Dashboard talks only to API.
- API and bot share data contracts through `packages/contracts`.
- Data access should be centralized in `packages/db`.
- Async tasks are offloaded through `packages/queue` + workers.

## Recommended Next Files
- Root `docker-compose.yml` and environment templates.
- Workspace package manager config (`pnpm-workspace.yaml` or equivalent).
- ORM schema in `packages/db/prisma/schema.prisma`.
- Bot module manifest interfaces in `packages/plugin-sdk`.
- API auth/session middleware in `apps/api/src/modules/auth`.

# Full Stack Setup

## Services
- Bot: `apps/bot`
- API: `apps/api`
- Web: `apps/web`
- Worker: `apps/api/src/workers`

## Local Setup
1. Copy env template:
```powershell
Copy-Item .env.example .env
```

2. Install dependencies:
```bash
pnpm install
```

3. Generate Prisma client and apply migrations:
```bash
pnpm db:generate
pnpm db:migrate
```

4. Register slash commands:
```bash
pnpm --filter @platform/bot register:commands
```

5. Start services in separate terminals:
```bash
pnpm dev:api
pnpm dev:bot
pnpm dev:web
pnpm dev:worker
```

## Docker Compose
```bash
docker compose up --build
```

## Implemented Core Capabilities
- Multi-tenant guild data model using Prisma.
- Dashboard login with User ID + password and cookie sessions.
- Guild-restricted API access for admin users.
- Module state enable/disable per guild.
- Bot slash and prefix command framework.
- Event handling for:
  - `messageCreate`
  - `interactionCreate`
  - `guildMemberAdd`
  - `guildMemberRemove`
  - `guildUpdate`
  - `messageDelete`
  - `messageUpdate`
  - `reactionAdd`/`reactionRemove` (via Discord message reaction events)
  - `voiceStateUpdate`
- Worker loop for scheduled task processing.

## Remaining Expansion Work
- Replace worker polling with Redis-backed BullMQ/Celery pipelines.
- Implement full UI forms per module section.
- Expand each module with full command/event feature set (moderation, tickets, giveaways, economy).
- Add integration/e2e/load tests and CI workflows.

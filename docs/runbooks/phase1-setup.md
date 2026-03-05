# Phase 1 Setup and Validation

## What Phase 1 Includes
- Prisma schema with core multi-tenant tables in `packages/db/prisma/schema.prisma`.
- Initial migration SQL in `packages/db/prisma/migrations/202603050001_init/migration.sql`.
- Bot slash command `/create-dashboard-admin` with:
  - Administrator permission check.
  - Guild/user upsert.
  - Existing account guard.
  - Secure password generation.
  - Argon2id hashing with bcrypt fallback.
  - Credentials sent by DM.
  - Audit logging and rollback if DM fails.

## Prerequisites
- Node.js 20+
- pnpm 9+

## Setup
1. Install dependencies:
```bash
pnpm install
```

2. Create `.env` from `.env.example` and set values:
- `DATABASE_URL` (default local SQLite file)
- `DISCORD_BOT_TOKEN`
- `DISCORD_CLIENT_ID`
- `DISCORD_GUILD_ID`

3. Generate Prisma client:
```bash
pnpm db:generate
```

4. Apply migration:
```bash
pnpm db:migrate
```

5. Register slash commands in your test guild:
```bash
pnpm --filter @platform/bot register:commands
```

6. Start bot:
```bash
pnpm --filter @platform/bot dev
```

## Validation Checklist
1. In Discord, run `/create-dashboard-admin` as a server administrator.
2. Confirm ephemeral success response.
3. Confirm DM with `User ID`, `Username`, and generated `Password`.
4. Confirm row in `DashboardAdmins` and `AuditLogs`.
5. Disable DMs and retry to verify rollback behavior.

## Security Notes
- Passwords are never stored plaintext.
- DM delivery is required; on DM failure, account creation is rolled back.
- Admin account uniqueness is enforced per `(discordUserId, guildId)`.

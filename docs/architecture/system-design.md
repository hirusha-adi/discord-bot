# Discord SaaS Platform Architecture

## 1. Goals
- Build a multi-tenant Discord bot SaaS platform similar to MEE6.
- Ensure each guild (server) has isolated configuration and runtime behavior.
- Support large scale (thousands of guilds) with sharding, workers, and horizontal scale.
- Keep all features available to all users (no premium tier).
- Start with SQLite3 for development and migrate to PostgreSQL in production without major refactor.

## 2. High-Level Services
1. `apps/bot` (Discord Gateway Service)
- Handles Discord events and command execution.
- Runs module event handlers from plugin registry.
- Publishes async jobs for heavy/slow workloads.

2. `apps/api` (REST Backend)
- Serves dashboard and admin APIs.
- Performs auth/session management.
- Enforces tenant boundaries and RBAC checks.

3. `apps/web` (Dashboard UI)
- Login with Discord User ID + password created by bot command.
- Server picker and module configuration pages.
- Real-time preview and write-through updates to API.

4. `workers` (inside `apps/api/src/workers` and/or dedicated worker image)
- Executes scheduled tasks, temp punishments, giveaway closes, analytics aggregation.
- Consumes Redis-backed queues.

5. `packages/db` (Data Layer)
- ORM schema and migrations.
- Repository helpers and transaction utilities.

6. `packages/plugin-sdk` + `apps/bot/src/modules/*`
- Module contract, lifecycle hooks, command registration, dashboard metadata.

## 3. Runtime Topology
- Discord Gateway shards -> Bot pods/processes.
- API pods/processes behind reverse proxy.
- Web frontend served by Node runtime or static edge output.
- Redis for cache, sessions, distributed locks, and queues.
- SQLite (dev only) local file.
- PostgreSQL (prod) managed database.

Recommended deployment unit (default): Docker Compose on one VM.
Scale path: split to multi-VM/Kubernetes while preserving service boundaries.

## 4. Tenant Isolation Model
Tenant key: `guild_id`.

Isolation rules:
- Every mutable entity includes `guild_id` unless truly global.
- API access requires authenticated admin session and guild membership in `DashboardAdmins`.
- Bot command execution validates guild permissions and module enablement.
- Data access layer requires explicit guild scoping helpers to avoid unscoped queries.

## 5. Authentication and Admin Provisioning
### 5.1 Admin Creation Flow (Discord)
1. User executes `/create-dashboard-admin`.
2. Bot verifies `Administrator` permission in that guild.
3. Bot checks existing `DashboardAdmins` record for `(guild_id, discord_user_id)`.
4. If absent, bot generates random strong password and username.
5. Password is hashed (Argon2id preferred, bcrypt fallback).
6. Record stored in `DashboardAdmins`.
7. Credentials sent only through Discord DM.
8. Action written to `AuditLogs`.

### 5.2 Dashboard Login Flow
1. User submits `discord_user_id` + password.
2. API validates hash and account status.
3. API creates secure session (HTTP-only cookie, secure, same-site).
4. API returns guild list from `DashboardAdmins` for that user.
5. Every dashboard route includes guild context and authorization checks.

## 6. Data Architecture (ORM)
Core entities:
- `Guilds`
- `GuildSettings`
- `GuildModules`
- `Users`
- `DashboardAdmins`
- `Roles`
- `Permissions`
- `LevelingData`
- `ModerationLogs`
- `Automations`
- `CustomCommands`
- `ReactionRoles`
- `ScheduledTasks`
- `WelcomeMessages`
- `TempBans`
- `Giveaways`
- `Tickets`
- `EconomyBalances`
- `EconomyTransactions`
- `AuditLogs`
- `AdminSessions`

Schema guidelines:
- Add `created_at`, `updated_at` on mutable tables.
- Use composite indexes like `(guild_id, user_id)` for hot paths.
- Use soft deletes where auditability matters.
- Keep IDs stable as strings for Discord snowflakes.

## 7. Module/Plugin System
### 7.1 Module Contract
Each module exports:
- `manifest` (id, name, version, required permissions)
- `registerCommands(registry)`
- `registerEvents(bus)`
- `registerApiRoutes(router)` (optional)
- `dashboardSchema` for UI form generation
- `migrations` or schema extensions through shared ORM package

### 7.2 Per-Guild Enablement
- `GuildModules` stores enabled state and module config version.
- Bot checks module enabled before command/event handling.
- Dashboard toggles modules and persists config atomically.

## 8. Feature Domain Design
1. Moderation
- Commands: ban, kick, mute, timeout, warn, softban, unban.
- Stores case history, mod notes, appeal notes, temporary actions.

2. Auto Moderation
- Bad words, spam, invites, caps, rate limits, link whitelist.
- Real-time rule evaluation in bot process; expensive checks offloaded to worker.

3. Welcome/Goodbye
- Template engine with safe variables.
- Optional image generation via queue worker.

4. Leveling
- XP accrual with cooldown and anti-spam filters.
- Leaderboards pre-aggregated for fast dashboard load.

5. Custom Commands
- Stored command definitions with variable interpolation and constraints.

6. Reaction Roles
- Message-reaction mapping and optional button/select role flows.

7. Automation
- Condition-action rule engine with deterministic execution limits.

8. Logging
- Event-specific log sinks and configurable channels per guild.

9. Economy
- Ledger-based transaction model for consistency and auditability.

10. Giveaways
- Worker-driven scheduling and winner selection with reroll support.

11. Tickets
- Channel provisioning, transcript generation, close/reopen lifecycle.

12. Analytics
- Time-series aggregates for dashboard charts and usage metrics.

## 9. Command Framework (Bot)
Pipeline:
1. Parse interaction/prefix command.
2. Resolve guild + member context.
3. Permission + module checks.
4. Cooldown + anti-abuse checks.
5. Execute command handler.
6. Emit audit/log events.
7. Handle errors with user-safe responses + internal telemetry.

## 10. Event Handling
Supported events:
- `messageCreate`
- `interactionCreate`
- `guildMemberAdd`
- `guildMemberRemove`
- `guildUpdate`
- `messageDelete`
- `messageUpdate`
- `reactionAdd`
- `reactionRemove`
- `voiceStateUpdate`

Design:
- Event bus fan-out to enabled modules.
- Backpressure and debounce for bursty events.
- Idempotency keys where duplicate gateway events are possible.

## 11. API Architecture
Suggested layering:
- `routes` -> `controllers` -> `services` -> `repositories`.
- Shared request validation schema (zod/class-validator/pydantic).
- All endpoints require auth except health and login.

Key endpoint groups:
- `/auth/*`
- `/guilds/*`
- `/modules/*`
- `/settings/*`
- `/analytics/*`
- `/admin/*` (platform owner only)

## 12. Queue and Worker Architecture
Redis queues (BullMQ/Celery equivalent):
- `scheduled-tasks`
- `moderation-expirations`
- `welcome-image-render`
- `giveaway-finalize`
- `analytics-rollup`
- `ticket-transcript`

Worker requirements:
- Retry policy with dead-letter queue.
- Idempotent handlers.
- Structured logs with correlation IDs.

## 13. Security Controls
- Argon2id/bcrypt password hashing.
- Session cookies: HTTP-only, secure, same-site.
- CSRF protection for dashboard forms.
- Per-route and per-user rate limiting.
- Input validation and output encoding.
- Secrets via env vars and secret manager in production.
- Audit logs for admin and moderation actions.
- Lockout/backoff policy for repeated failed logins.

## 14. Scalability Strategy
Phase 1:
- Single VM, Docker Compose, SQLite, Redis.

Phase 2:
- Move DB to PostgreSQL.
- Enable multiple bot processes with sharding.
- Scale API horizontally behind reverse proxy.

Phase 3:
- Separate worker pool autoscaling.
- Optional Kubernetes and managed Redis/Postgres.
- Read replicas and analytics pipeline hardening.

## 15. Observability and Operations
- Structured logs (JSON).
- Metrics: command latency, error rates, queue lag, shard health, API p95.
- Health endpoints for bot/api/worker.
- Alerting on auth failures, worker backlog, shard disconnects.

## 16. CI/CD
- Lint + typecheck + unit tests on PR.
- Integration tests with ephemeral DB.
- Build/push Docker images.
- Deploy with environment-specific compose overrides.

## 17. Migration Path: SQLite -> PostgreSQL
- Keep ORM as single source of truth.
- Avoid SQLite-only SQL semantics in app code.
- Use UUID/text and explicit timestamp behavior compatible with both engines.
- Run migration diff validation in CI against both providers.

## 18. Global Admin Panel
Capabilities:
- View all guilds and health state.
- Disable abusive guilds (soft block + reason).
- Monitor command volumes and errors.
- Inspect audit and moderation summary logs.

Access:
- Separate owner role and stricter session policy.
- Explicit break-glass audit trail for sensitive actions.

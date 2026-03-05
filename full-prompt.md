## Improved Prompt for AI Agent (Step-by-step, explicit)

You are a senior software architect + engineer. Build a **production-ready Discord bot platform** with a **web dashboard** and **per-guild customization**. The system must be modular, secure, and scalable to many guilds.

### 0) Non-negotiable constraints (read first)

1. **Discord bot:** Python **discord.py**, use **slash commands by default**, enable **all intents**.
2. **Backend API:** Python **FastAPI**.
3. **Frontend:** **Next.js + React (JavaScript only, NOT TypeScript)**.
4. **Database:** **SQLite3 now**, must be **migratable to Postgres later**. Use **SQLAlchemy** + migrations (Alembic).
5. **Dockerize everything** with a dev + prod setup.
6. Build must include a **README.md** with exact commands for:

   * running dev locally
   * deploying to a single VPS (for now)

---

## 1) Deliverables (what you must produce)

Produce:

1. A complete repo structure with separate services:

   * `bot/` (discord bot)
   * `api/` (FastAPI)
   * `web/` (Next.js)
   * `infra/` (docker, nginx/caddy config if needed, scripts)
2. Database models + migration setup.
3. Auth system (local + Discord OAuth).
4. Guild/module configuration system.
5. Working implementations for the modules listed below.
6. A working Docker Compose stack for dev + a production deployment path.

---

## 2) Architecture and responsibilities (must follow)

### 2.1 Services

1. **Bot service (discord.py)**

   * Connects to DB (via SQLAlchemy or via API; pick ONE approach and justify briefly).
   * Handles Discord events + slash commands.
   * Reads guild configuration from DB.
2. **API service (FastAPI)**

   * Provides REST endpoints for the dashboard.
   * Handles auth, session tokens, RBAC, CRUD for modules/config.
3. **Web dashboard (Next.js)**

   * Login page (local + “Login with Discord”).
   * After login: list guilds user can manage.
   * Guild page: stats + modules + config UI.
4. **DB**

   * SQLAlchemy models with explicit relationships.
   * Alembic migrations.
   * Compatible schema strategy for future Postgres.

### 2.2 Security + permissions

1. Discord OAuth must request scopes needed to:

   * Identify user
   * Read guilds
   * Determine whether user has admin rights (or Manage Guild)
2. Only show a guild in the dashboard if:

   * the logged-in user is an **admin** (or has **Manage Guild**) **AND**
   * the bot is present in that guild
3. Implement RBAC:

   * “Guild admin” permissions derived from Discord perms.
   * Dashboard actions must verify the user is authorized for that guild.

---

## 3) Database design (explicit tables you must create)

Create SQLAlchemy models (names can vary, but must cover):

1. `User` (local auth + Discord-linked account)
2. `Guild` (discord guild id, name, etc.)
3. `GuildUser` (mapping user ↔ guild with role/permission cache)
4. `Module` or `FeatureFlag` (per-guild enable/disable + settings JSON)
5. `WelcomeConfig` (enabled, markdown text, optional image URLs/attachments metadata, target rules)
6. `LeaveConfig` (enabled, markdown text, optional image)
7. `VerificationConfig` (enabled, role ids to grant, etc.)
8. `RegisteredMemberList` (guild id, uploaded file metadata, hash, uploaded_at)
9. `RegisteredMemberEmail` (guild id, email; indexed; unique per guild)
10. `AuditLogConfig` (enabled, logging destination: channel id or “dashboard only”)
11. `MessageAuditEvent` (guild id, type edit/delete, author id, channel id, message id, old/new content, timestamps)
12. `AnnouncementConfig` (enabled, default channel id, allowed roles to ping, etc.)
13. `ScheduledAnnouncement` (guild id, content markdown, images, ping rules, scheduled_at, status)

Must include indexes for:

* `(guild_id, email)` on registered emails
* `(guild_id, message_id)` on audit logs
* `(guild_id, scheduled_at)` on announcements

---

## 4) Modules and exact behaviors (implement these exactly)

### 4.1 Welcome DM module (optional + configurable)

**Goal:** When a member joins a guild, optionally DM them a welcome message.
Steps:

1. Add a per-guild toggle: `welcome_dm_enabled`.
2. In the dashboard, provide a **Markdown editor** for welcome text.
3. Support optional images (store image references and send them in DM).
4. On member join event:

   * If enabled, DM the member with rendered markdown-compatible formatting for Discord.

### 4.2 Leave DM module (optional + configurable)

Same as welcome DM, but triggers on member leave.

### 4.3 Verification module (email-based role assignment)

**Goal:** Member runs `/verify` → enters email → if email is in registered list → grant configured role(s).

Steps:

1. Dashboard:

   * Toggle `verification_enabled`
   * Configure one or multiple role IDs to grant when verified
2. Bot:

   * Implement `/verify` slash command:

     1. Prompt user for email (private interaction)
     2. Normalize email (trim + lowercase)
     3. Look up in `RegisteredMemberEmail` for that guild
     4. If found: assign configured role(s)
     5. If not found: respond with a failure message (no role changes)
3. Admin import:

   * Implement an admin-only slash command: `/add-members-list` that accepts a **text file** of emails (1 per line).
   * Also implement dashboard upload of the same file (per guild).
4. After upload (command OR dashboard):

   * Parse emails safely, validate format, dedupe, store.
   * Then run a **sync** operation:

     * For every guild member:

       * If member’s verified email exists in list → ensure roles are present
       * If not in list → remove configured roles (unless role removal is disabled; default is enabled)
5. Add a dashboard button: **“Run role sync now”** (admin-only) that triggers the same sync on-demand.
6. Handle lifecycle:

   * If a user leaves or is banned, clean up any verification linkage for that guild as needed (no orphaned state that causes incorrect role assignment later).

### 4.4 Message audit logging module (optional)

**Goal:** Log message edits and deletes per guild.

Steps:

1. Dashboard:

   * Toggle `audit_logging_enabled`
   * Choose delivery:

     * Option A: send logs to a selected Discord channel
     * Option B: store logs and show in dashboard only
2. Bot:

   * On message edit:

     * Record old + new content (when available)
   * On message delete:

     * Record deleted content if cached/available, otherwise store metadata
3. Provide dashboard view:

   * Filter by channel, user, event type, date range

### 4.5 Announcements module (manual + scheduled)

**Goal:** Admins can create announcements from dashboard, send now or schedule.

Steps:

1. Dashboard:

   * Rich text editor (Markdown acceptable if you prefer; must support images)
   * Option to ping:

     * everyone OR specific roles
   * Ping syntax must work from within message content (e.g., role mentions)
2. Sending:

   * “Send now” posts to configured channel
3. Scheduling:

   * Create scheduled jobs (background worker) that sends at `scheduled_at`
   * Track status: pending/sent/failed
4. Bot/API:

   * Ensure posting respects guild config and permissions

### 4.6 Guild dashboard landing experience

When user selects a guild in the dashboard:

1. Show top-level stats (member count, join/leave metrics if available, enabled modules)
2. Show a module list with toggles + configuration links.

---

## 5) Core bot commands (must exist)

Implement as slash commands:

1. `/ping`
2. `/help`
3. `/uptime`
4. `/verify` (module-gated)
5. `/add-members-list` (admin-only, module-gated)

---

## 6) Background workers

Implement a worker process for:

1. Scheduled announcements
2. Verification role sync jobs (when triggered)
3. Any retry logic for failed sends

---

## 7) Docker + environments (must be explicit)

1. Provide `docker-compose.yml` for development:

   * bot
   * api
   * web
   * db (sqlite volume)
2. Provide production docker-compose (single VPS) with:

   * persistent volumes
   * environment variables via `.env`
3. Document required env vars:

   * Discord bot token
   * Discord OAuth client id/secret/redirect URL
   * JWT/session secrets
   * DB connection strings (sqlite + future postgres)

---

## 8) Testing + acceptance checklist (you must verify)

Before final output, ensure:

1. OAuth login works, guild list filters correctly (only admin guilds where bot exists).
2. Welcome DM triggers on join when enabled.
3. Leave DM triggers on leave when enabled.
4. `/verify` assigns roles correctly only when email is in list.
5. Uploading member list triggers role sync correctly.
6. “Run role sync now” works.
7. Edit/delete logging works and can be viewed (channel or dashboard).
8. Announcements send now + schedule works.
9. Everything runs via Docker Compose with clear README steps.

---

## 9) Output format requirements

1. Provide the repo tree.
2. Provide key code files (or all code if possible).
3. Provide README.md with dev + prod steps.
4. Provide a brief explanation of design decisions (max ~15 lines).

---

If you want, I can also rewrite this into a **“System prompt + Developer prompt + Task list”** format (agents like Cursor/Devin-style tend to follow that even more reliably).



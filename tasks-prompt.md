## Task List with Explicit Implementation Stages

Use these stages exactly. When asked “Implement Stage N”, do only that stage, and ensure it runs.

---

## Stage 0 — Repo scaffolding + Docker baseline

**Goal:** A runnable multi-service skeleton with Docker Compose.

**Tasks**

1. Create repo structure:

   * `bot/`, `api/`, `web/`, `infra/`
2. Add dev `docker-compose.yml` to run:

   * bot (placeholder app)
   * api (FastAPI hello endpoint)
   * web (Next.js hello page)
   * shared `.env.example`
3. Add minimal production compose file template in `infra/` (can be incomplete but syntactically correct).
4. Add README.md (initial) with:

   * prerequisites
   * `docker compose up --build`
   * how to run each service logs

**Acceptance checks**

* `docker compose up --build` starts all services without crashing.
* Web loads a page, API returns 200 for `/health`.

---

## Stage 1 — Database layer (SQLAlchemy + Alembic) + core models

**Goal:** DB schema established and migratable.

**Tasks**

1. In `api/`, set up:

   * SQLAlchemy engine/session
   * Alembic migrations
   * config for SQLite now, Postgres later
2. Create core models + migrations:

   * User (local + discord linked)
   * Guild
   * GuildUser (membership/permission cache)
   * Module toggles/config tables for:

     * WelcomeConfig
     * LeaveConfig
     * VerificationConfig
     * RegisteredMemberList + RegisteredMemberEmail
     * AuditLogConfig + MessageAuditEvent
     * AnnouncementConfig + ScheduledAnnouncement
3. Add indexes required.
4. Add API endpoint `/health` and `/db/ping` (simple DB query).

**Acceptance checks**

* `alembic upgrade head` works inside docker.
* Tables exist, and `/db/ping` returns OK.

---

## Stage 2 — Authentication: local login + Discord OAuth

**Goal:** Dashboard login works and backend enforces identity.

**Tasks**

1. Implement local auth in API:

   * password hashing
   * JWT/session token (choose one and document)
2. Implement Discord OAuth2 flow in API:

   * login redirect endpoint
   * callback endpoint
   * store discord user id + tokens minimally (don’t store if not needed; prefer short-lived)
3. Implement web login UI:

   * local login form
   * “Login with Discord” button
4. Add middleware/guards in API to protect routes.

**Acceptance checks**

* Can login locally and access protected endpoint.
* Discord OAuth completes and returns a session.
* Session persists in browser (cookie or token as designed).

---

## Stage 3 — Guild discovery + permissions filtering

**Goal:** Web lists only manageable guilds where bot is present.

**Tasks**

1. API: endpoint `GET /guilds`:

   * uses Discord OAuth token to fetch user guilds
   * filters by Admin/Manage Guild
   * cross-check bot membership in guilds (Discord API or stored cache)
2. Web: guild selection page showing filtered guild list.
3. API: endpoint `GET /guilds/{guild_id}/overview`:

   * basic stats placeholder (member count if available later; otherwise stub with TODO)
   * enabled modules list + toggles (read-only in this stage is acceptable)

**Acceptance checks**

* Guild list is filtered correctly.
* Clicking a guild loads overview page without errors.

---

## Stage 4 — Module framework + per-guild toggles/config CRUD

**Goal:** A consistent way to enable/disable modules and edit config via dashboard.

**Tasks**

1. API: CRUD endpoints per module:

   * get config
   * update config
   * enable/disable toggle
2. Web: per-guild “Modules” page:

   * list modules
   * toggles
   * configuration forms:

     * markdown editor for welcome/leave (basic textarea OK; markdown preview optional)
     * role selection inputs can be raw role IDs for now (role picker later)

**Acceptance checks**

* Toggle changes persist in DB.
* Config updates persist and reload correctly.

---

## Stage 5 — Bot ↔ DB integration + core slash commands

**Goal:** Bot runs with DB access and supports `/ping`, `/help`, `/uptime`.

**Tasks**

1. Bot connects to DB (same schema) and reads per-guild module settings.
2. Implement slash commands:

   * `/ping`
   * `/help`
   * `/uptime`
3. Ensure bot starts cleanly in Docker and can access DB.

**Acceptance checks**

* Bot online, commands respond.
* No DB connection errors.

---

## Stage 6 — Welcome/Leave DM modules

**Goal:** DMs send on join/leave when enabled.

**Tasks**

1. On member join:

   * if enabled, send markdown-ish message + optional images
2. On member leave:

   * same behavior
3. Add minimal dashboard config fields needed (already mostly done).

**Acceptance checks**

* Toggle on => DM sends
* Toggle off => nothing sends

---

## Stage 7 — Verification module: `/verify` + member list import + role sync

**Goal:** Email verification and automated role management works.

**Tasks**

1. Bot: `/verify`

   * prompt email privately
   * normalize + lookup in RegisteredMemberEmail
   * grant configured roles
   * store verification linkage (member_id ↔ email) if needed
2. Bot: `/add-members-list` (admin-only)

   * accept text file
   * parse/validate/dedupe
   * store list + trigger sync
3. Web:

   * upload members list file
   * “Run role sync now” button
4. Sync logic:

   * iterate guild members
   * ensure roles based on membership list
   * remove roles for non-members (if configured)
5. Cleanup handling:

   * on member leave/ban: remove linkage/state safely

**Acceptance checks**

* `/verify` grants roles only for listed emails.
* Upload triggers sync and roles update accordingly.
* Manual sync button works.

---

## Stage 8 — Message audit logging (edits/deletes)

**Goal:** Record edit/delete events and show them somewhere.

**Tasks**

1. Bot listens for:

   * message edit
   * message delete
2. Store MessageAuditEvent in DB.
3. If configured with log channel:

   * send formatted log embed/message
   * else: dashboard-only storage
4. Web page to view logs with basic filters.

**Acceptance checks**

* Events appear in DB and (optionally) in configured channel.

---

## Stage 9 — Announcements: send now + scheduling + worker

**Goal:** Admins can create announcements now or scheduled.

**Tasks**

1. API endpoints to create announcements and scheduled announcements.
2. Worker service to dispatch scheduled announcements.
3. Bot (or API) posts messages:

   * supports role mentions and @everyone when allowed
   * supports images
4. Web UI:

   * editor + schedule picker
   * status display (pending/sent/failed)

**Acceptance checks**

* “Send now” posts correctly.
* Scheduled posts fire at the right time.
* Failures are tracked.

---

## Stage 10 — Hardening + deployment polish

**Goal:** Production readiness for single VPS deployment.

**Tasks**

1. Production compose finalized.
2. Add logging, retries, rate limit handling basics.
3. Add backup/volume notes for DB.
4. Security review checklist in README.

**Acceptance checks**

* End-to-end flow works on a VPS with one command deployment (documented).

---

## How you should use this staged plan

When I say “Implement Stage 1”, you must:

* implement only Stage 1 tasks
* keep Stage 0 working
* output only touched files
* include commands + acceptance checklist

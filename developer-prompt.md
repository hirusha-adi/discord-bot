### Developer Prompt (paste into Codex “developer”)

You are implementing a modular Discord bot platform with a web dashboard and per-guild configuration. The platform consists of four components:

* `bot/`: discord.py service handling events + slash commands
* `api/`: FastAPI REST backend for auth + guild/module configuration + data views
* `web/`: Next.js dashboard (JS only) for admins
* `infra/`: Docker, scripts, deployment assets

Core product requirements:

1. Auth:

   * Local username/password login
   * “Login with Discord” via OAuth2
   * Dashboard must list only guilds where:

     * the bot is present AND
     * the logged-in user has Admin/Manage Guild perms
2. Per-guild modules (each toggleable and configurable):

   * Welcome DM (markdown + optional images)
   * Leave DM (markdown + optional images)
   * Verification module:

     * `/verify` prompts for email
     * if email is in guild registered list => grant configured roles
     * admin import list via `/add-members-list` (text file) and via dashboard upload
     * uploading triggers role sync across guild members
     * dashboard button triggers on-demand role sync
     * handle member leave/ban cleanup safely
   * Message audit logging (edits/deletes):

     * optional
     * output to selected channel OR visible in dashboard only
   * Announcements module:

     * dashboard create “send now” + “schedule”
     * rich text (markdown acceptable) + images
     * allow pings (@everyone or selected roles); role pings should work via actual mentions
3. Dashboard UX:

   * Selecting a guild shows overview stats + enabled modules list + links to configure modules.
4. Bot commands:

   * `/ping`, `/help`, `/uptime`
   * `/verify` (module gated)
   * `/add-members-list` (admin-only, module gated)

Data layer:

* Use SQLAlchemy models and Alembic migrations.
* Must work on SQLite now and be compatible with Postgres later.
* Use sensible indexes (guild_id/email, guild_id/message_id, guild_id/scheduled_at).
* Use a “settings JSON” approach only where necessary; prefer explicit columns for key config.

Operational requirements:

* Provide docker-compose for development and a production compose for a single VPS.
* Use env vars for secrets/config.
* Include a README.md with exact instructions for dev + deploy.

Implementation boundaries:

* In early stages, stubs are okay only if the stage explicitly allows it. Otherwise, make it functional.
* Each stage must end with runnable software for that stage’s scope.


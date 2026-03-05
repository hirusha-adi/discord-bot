import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import UTC, datetime

import discord
from discord.ext import commands
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_TEST_GUILD_ID = os.getenv("DISCORD_TEST_GUILD_ID", "").strip()

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)

start_time = datetime.now(UTC)
logger = logging.getLogger("bot")


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="ts=%(asctime)s level=%(levelname)s service=bot logger=%(name)s msg=%(message)s",
    )


def _print_to_logger(*args, **kwargs) -> None:  # noqa: ARG001
    logger.info(" ".join(str(arg) for arg in args))


print = _print_to_logger  # noqa: A001


def create_db_engine():
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, future=True, pool_pre_ping=True, connect_args=connect_args)


engine = create_db_engine()


def db_startup_ping() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("db_startup_ping_ok")
        return True
    except SQLAlchemyError as exc:
        logger.exception("db_startup_ping_failed error=%s", exc)
        return False


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _is_valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.match(value))


def _parse_json_list(raw_value) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            return []
    return []


def _parse_emails_from_text(text_data: str) -> list[str]:
    emails: set[str] = set()
    for raw_line in text_data.splitlines():
        candidate = _normalize_email(raw_line)
        if not candidate:
            continue
        if _is_valid_email(candidate):
            emails.add(candidate)
    return sorted(emails)


def _truncate_text(value: str | None, max_len: int = 1500) -> str | None:
    if value is None:
        return None
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _ensure_guild_row(discord_guild_id: str, guild_name: str) -> int:
    with engine.begin() as connection:
        guild_row = connection.execute(
            text("SELECT id FROM guilds WHERE discord_guild_id = :discord_guild_id"),
            {"discord_guild_id": discord_guild_id},
        ).mappings().first()

        if guild_row:
            connection.execute(
                text(
                    """
                    UPDATE guilds
                    SET name = :name, bot_present = 1
                    WHERE id = :id
                    """
                ),
                {"id": guild_row["id"], "name": guild_name},
            )
            return int(guild_row["id"])

        inserted = connection.execute(
            text(
                """
                INSERT INTO guilds (discord_guild_id, name, bot_present, created_at, updated_at)
                VALUES (:discord_guild_id, :name, 1, :now, :now)
                """
            ),
            {"discord_guild_id": discord_guild_id, "name": guild_name, "now": datetime.now(UTC)},
        )
        return int(inserted.lastrowid)


def _get_audit_log_config(discord_guild_id: str) -> dict:
    query = text(
        """
        SELECT
            COALESCE(a.enabled, 0) AS enabled,
            a.destination_type AS destination_type,
            a.log_channel_id AS log_channel_id
        FROM guilds g
        LEFT JOIN audit_log_configs a ON a.guild_id = g.id
        WHERE g.discord_guild_id = :discord_guild_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query, {"discord_guild_id": discord_guild_id}).mappings().first()

    if not row:
        return {"enabled": False, "destination_type": "dashboard", "log_channel_id": None}

    return {
        "enabled": bool(row["enabled"]),
        "destination_type": row["destination_type"] or "dashboard",
        "log_channel_id": row["log_channel_id"],
    }


def _store_message_audit_event(
    guild_row_id: int,
    event_type: str,
    channel_discord_id: str | None,
    message_id: str,
    author_discord_id: str | None,
    old_content: str | None,
    new_content: str | None,
) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO message_audit_events (
                    guild_id,
                    event_type,
                    author_discord_id,
                    channel_discord_id,
                    message_id,
                    old_content,
                    new_content,
                    occurred_at
                )
                VALUES (
                    :guild_id,
                    :event_type,
                    :author_discord_id,
                    :channel_discord_id,
                    :message_id,
                    :old_content,
                    :new_content,
                    :occurred_at
                )
                """
            ),
            {
                "guild_id": guild_row_id,
                "event_type": event_type,
                "author_discord_id": author_discord_id,
                "channel_discord_id": channel_discord_id,
                "message_id": message_id,
                "old_content": _truncate_text(old_content),
                "new_content": _truncate_text(new_content),
                "occurred_at": datetime.now(UTC),
            },
        )


async def _send_audit_log_message(
    guild: discord.Guild,
    config: dict,
    event_type: str,
    channel_discord_id: str | None,
    message_id: str,
    author_discord_id: str | None,
    old_content: str | None,
    new_content: str | None,
) -> None:
    log_channel_id = config.get("log_channel_id")
    if not log_channel_id:
        return

    if not str(log_channel_id).isdigit():
        print(f"[bot] Invalid audit log channel id for guild {guild.id}: {log_channel_id}")
        return

    channel = guild.get_channel(int(log_channel_id))
    if channel is None:
        try:
            fetched = await guild.fetch_channel(int(log_channel_id))
        except discord.HTTPException as exc:
            print(f"[bot] Failed to fetch audit log channel {log_channel_id} in guild {guild.id}: {exc}")
            return
        channel = fetched

    if not isinstance(channel, discord.TextChannel):
        print(f"[bot] Audit log channel {log_channel_id} is not a text channel in guild {guild.id}")
        return

    embed = discord.Embed(
        title="Message Edited" if event_type == "edit" else "Message Deleted",
        color=discord.Color.orange() if event_type == "edit" else discord.Color.red(),
        timestamp=datetime.now(UTC),
    )
    embed.add_field(name="Message ID", value=message_id, inline=False)
    embed.add_field(name="Channel ID", value=channel_discord_id or "unknown", inline=False)
    embed.add_field(name="Author ID", value=author_discord_id or "unknown", inline=False)
    embed.add_field(name="Old Content", value=_truncate_text(old_content, 900) or "(none)", inline=False)
    if event_type == "edit":
        embed.add_field(name="New Content", value=_truncate_text(new_content, 900) or "(none)", inline=False)

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        print(f"[bot] Missing permission to send audit logs in channel {log_channel_id} (guild {guild.id})")
    except discord.HTTPException as exc:
        print(f"[bot] Failed to send audit log message in guild {guild.id}: {exc}")


async def _handle_message_audit_event(
    guild: discord.Guild | None,
    guild_id: int | None,
    guild_name: str | None,
    event_type: str,
    channel_discord_id: str | None,
    message_id: str,
    author_discord_id: str | None,
    old_content: str | None,
    new_content: str | None,
    is_author_bot: bool,
) -> None:
    if guild is None and guild_id is None:
        return

    if is_author_bot:
        return

    effective_guild_id = str(guild.id if guild is not None else guild_id)
    effective_guild_name = guild.name if guild is not None else (guild_name or f"Guild {effective_guild_id}")

    config = _get_audit_log_config(effective_guild_id)
    if not config["enabled"]:
        return

    guild_row_id = _ensure_guild_row(effective_guild_id, effective_guild_name)
    _store_message_audit_event(
        guild_row_id=guild_row_id,
        event_type=event_type,
        channel_discord_id=channel_discord_id,
        message_id=message_id,
        author_discord_id=author_discord_id,
        old_content=old_content,
        new_content=new_content,
    )

    if guild is not None and config.get("log_channel_id"):
        await _send_audit_log_message(
            guild=guild,
            config=config,
            event_type=event_type,
            channel_discord_id=channel_discord_id,
            message_id=message_id,
            author_discord_id=author_discord_id,
            old_content=old_content,
            new_content=new_content,
        )


def _get_verification_config(discord_guild_id: str) -> dict:
    query = text(
        """
        SELECT
            COALESCE(v.enabled, 0) AS enabled,
            v.role_ids AS role_ids,
            COALESCE(v.remove_roles_when_unlisted, 1) AS remove_roles_when_unlisted
        FROM guilds g
        LEFT JOIN verification_configs v ON v.guild_id = g.id
        WHERE g.discord_guild_id = :discord_guild_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query, {"discord_guild_id": discord_guild_id}).mappings().first()

    if not row:
        return {"enabled": False, "role_ids": [], "remove_roles_when_unlisted": True}

    role_ids = []
    for role_id in _parse_json_list(row["role_ids"]):
        if role_id.isdigit():
            role_ids.append(int(role_id))

    return {
        "enabled": bool(row["enabled"]),
        "role_ids": role_ids,
        "remove_roles_when_unlisted": bool(row["remove_roles_when_unlisted"]),
    }


def _email_is_registered(discord_guild_id: str, email: str) -> bool:
    query = text(
        """
        SELECT 1
        FROM registered_member_emails e
        JOIN guilds g ON g.id = e.guild_id
        WHERE g.discord_guild_id = :discord_guild_id
          AND e.email = :email
        LIMIT 1
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "discord_guild_id": discord_guild_id,
                "email": email,
            },
        ).first()

    return row is not None


def _upsert_verification_link(discord_guild_id: str, guild_name: str, member_discord_id: str, email: str) -> None:
    guild_row_id = _ensure_guild_row(discord_guild_id, guild_name)

    with engine.begin() as connection:
        existing = connection.execute(
            text(
                """
                SELECT id
                FROM verification_links
                WHERE guild_id = :guild_id
                  AND member_discord_id = :member_discord_id
                """
            ),
            {"guild_id": guild_row_id, "member_discord_id": member_discord_id},
        ).mappings().first()

        now = datetime.now(UTC)
        if existing:
            connection.execute(
                text(
                    """
                    UPDATE verification_links
                    SET email = :email, verified_at = :verified_at
                    WHERE id = :id
                    """
                ),
                {"id": existing["id"], "email": email, "verified_at": now},
            )
        else:
            connection.execute(
                text(
                    """
                    INSERT INTO verification_links (guild_id, member_discord_id, email, verified_at)
                    VALUES (:guild_id, :member_discord_id, :email, :verified_at)
                    """
                ),
                {
                    "guild_id": guild_row_id,
                    "member_discord_id": member_discord_id,
                    "email": email,
                    "verified_at": now,
                },
            )


def _remove_verification_link(discord_guild_id: str, member_discord_id: str) -> None:
    with engine.begin() as connection:
        guild_row = connection.execute(
            text("SELECT id FROM guilds WHERE discord_guild_id = :discord_guild_id"),
            {"discord_guild_id": discord_guild_id},
        ).mappings().first()

        if not guild_row:
            return

        connection.execute(
            text(
                """
                DELETE FROM verification_links
                WHERE guild_id = :guild_id
                  AND member_discord_id = :member_discord_id
                """
            ),
            {"guild_id": guild_row["id"], "member_discord_id": member_discord_id},
        )


def _import_registered_emails(
    discord_guild_id: str,
    guild_name: str,
    filename: str,
    file_hash: str,
    emails: list[str],
) -> int:
    guild_row_id = _ensure_guild_row(discord_guild_id, guild_name)

    with engine.begin() as connection:
        list_insert = connection.execute(
            text(
                """
                INSERT INTO registered_member_lists (guild_id, source_type, filename, file_hash, uploaded_at)
                VALUES (:guild_id, :source_type, :filename, :file_hash, :uploaded_at)
                """
            ),
            {
                "guild_id": guild_row_id,
                "source_type": "bot_command",
                "filename": filename,
                "file_hash": file_hash,
                "uploaded_at": datetime.now(UTC),
            },
        )
        member_list_id = int(list_insert.lastrowid)

        # Replacement strategy: each import fully refreshes guild registered emails.
        connection.execute(
            text("DELETE FROM registered_member_emails WHERE guild_id = :guild_id"),
            {"guild_id": guild_row_id},
        )

        for email in emails:
            connection.execute(
                text(
                    """
                    INSERT INTO registered_member_emails (guild_id, member_list_id, email, created_at)
                    VALUES (:guild_id, :member_list_id, :email, :created_at)
                    """
                ),
                {
                    "guild_id": guild_row_id,
                    "member_list_id": member_list_id,
                    "email": email,
                    "created_at": datetime.now(UTC),
                },
            )

    return guild_row_id


def _create_sync_request(
    guild_row_id: int,
    source: str,
    requested_by_member_discord_id: str | None = None,
    requested_by_user_id: int | None = None,
) -> int:
    with engine.begin() as connection:
        inserted = connection.execute(
            text(
                """
                INSERT INTO verification_sync_requests (
                    guild_id,
                    requested_by_user_id,
                    requested_by_member_discord_id,
                    source,
                    status,
                    requested_at
                ) VALUES (
                    :guild_id,
                    :requested_by_user_id,
                    :requested_by_member_discord_id,
                    :source,
                    'pending',
                    :requested_at
                )
                """
            ),
            {
                "guild_id": guild_row_id,
                "requested_by_user_id": requested_by_user_id,
                "requested_by_member_discord_id": requested_by_member_discord_id,
                "source": source,
                "requested_at": datetime.now(UTC),
            },
        )
        return int(inserted.lastrowid)


def _set_sync_request_status(
    request_id: int,
    status_value: str,
    summary: dict | None = None,
    error_text: str | None = None,
) -> None:
    with engine.begin() as connection:
        now = datetime.now(UTC)
        updates = {
            "id": request_id,
            "status": status_value,
            "summary_json": json.dumps(summary) if summary is not None else None,
            "error_text": error_text,
            "now": now,
        }

        if status_value == "running":
            connection.execute(
                text(
                    """
                    UPDATE verification_sync_requests
                    SET status = :status,
                        started_at = :now,
                        error_text = NULL
                    WHERE id = :id
                    """
                ),
                updates,
            )
        elif status_value in {"completed", "failed"}:
            connection.execute(
                text(
                    """
                    UPDATE verification_sync_requests
                    SET status = :status,
                        finished_at = :now,
                        summary_json = :summary_json,
                        error_text = :error_text
                    WHERE id = :id
                    """
                ),
                updates,
            )


def _get_pending_sync_requests() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    r.id,
                    r.guild_id,
                    g.discord_guild_id
                FROM verification_sync_requests r
                JOIN guilds g ON g.id = r.guild_id
                WHERE r.status = 'pending'
                ORDER BY r.requested_at ASC
                """
            )
        ).mappings().all()

    return [dict(row) for row in rows]


def _get_sync_data_for_guild(guild_row_id: int) -> dict:
    with engine.connect() as connection:
        config_row = connection.execute(
            text(
                """
                SELECT
                    COALESCE(enabled, 0) AS enabled,
                    role_ids,
                    COALESCE(remove_roles_when_unlisted, 1) AS remove_roles_when_unlisted
                FROM verification_configs
                WHERE guild_id = :guild_id
                """
            ),
            {"guild_id": guild_row_id},
        ).mappings().first()

        valid_emails = {
            row["email"]
            for row in connection.execute(
                text("SELECT email FROM registered_member_emails WHERE guild_id = :guild_id"),
                {"guild_id": guild_row_id},
            ).mappings().all()
        }

        links = {
            row["member_discord_id"]: row["email"]
            for row in connection.execute(
                text("SELECT member_discord_id, email FROM verification_links WHERE guild_id = :guild_id"),
                {"guild_id": guild_row_id},
            ).mappings().all()
        }

    role_ids: list[int] = []
    if config_row and config_row["role_ids"] is not None:
        for role_id in _parse_json_list(config_row["role_ids"]):
            if role_id.isdigit():
                role_ids.append(int(role_id))

    return {
        "enabled": bool(config_row["enabled"]) if config_row else False,
        "remove_roles_when_unlisted": bool(config_row["remove_roles_when_unlisted"]) if config_row else True,
        "role_ids": role_ids,
        "valid_emails": valid_emails,
        "links": links,
    }


def _member_is_registered(member_id: int, links: dict[str, str], valid_emails: set[str]) -> bool:
    linked_email = links.get(str(member_id))
    if not linked_email:
        return False
    return linked_email in valid_emails


class Stage7Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.sync_worker_task: asyncio.Task | None = None

    async def setup_hook(self) -> None:
        if DISCORD_TEST_GUILD_ID:
            guild_obj = discord.Object(id=int(DISCORD_TEST_GUILD_ID))
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print(f"[bot] Synced slash commands to test guild {DISCORD_TEST_GUILD_ID}")
        else:
            await self.tree.sync()
            print("[bot] Synced global slash commands")

        self.sync_worker_task = asyncio.create_task(self.verification_sync_worker())

    async def close(self) -> None:
        if self.sync_worker_task is not None:
            self.sync_worker_task.cancel()
        await super().close()

    async def on_ready(self) -> None:
        print(f"[bot] Logged in as {self.user} (id={self.user.id if self.user else 'n/a'})")

    async def on_member_join(self, member: discord.Member) -> None:
        try:
            await send_configured_dm(member, "welcome")
        except SQLAlchemyError as exc:
            print(f"[bot] Welcome config DB read failed for guild {member.guild.id}: {exc}")

    async def on_member_remove(self, member: discord.Member) -> None:
        try:
            _remove_verification_link(str(member.guild.id), str(member.id))
        except SQLAlchemyError as exc:
            print(f"[bot] Verification cleanup on leave failed for guild {member.guild.id}: {exc}")

        try:
            await send_configured_dm(member, "leave")
        except SQLAlchemyError as exc:
            print(f"[bot] Leave config DB read failed for guild {member.guild.id}: {exc}")

    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member) -> None:
        try:
            _remove_verification_link(str(guild.id), str(user.id))
        except SQLAlchemyError as exc:
            print(f"[bot] Verification cleanup on ban failed for guild {guild.id}: {exc}")

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if payload.guild_id is None:
            return

        guild = self.get_guild(payload.guild_id)
        guild_name = guild.name if guild is not None else None

        cached_message = payload.cached_message
        old_content = cached_message.content if cached_message is not None else None
        is_author_bot = bool(cached_message.author.bot) if cached_message is not None else False
        author_discord_id = str(cached_message.author.id) if cached_message is not None else None

        new_content = payload.data.get("content")
        if cached_message is not None and new_content == old_content:
            return

        try:
            await _handle_message_audit_event(
                guild=guild,
                guild_id=payload.guild_id,
                guild_name=guild_name,
                event_type="edit",
                channel_discord_id=str(payload.channel_id) if payload.channel_id else None,
                message_id=str(payload.message_id),
                author_discord_id=author_discord_id,
                old_content=old_content,
                new_content=new_content,
                is_author_bot=is_author_bot,
            )
        except SQLAlchemyError as exc:
            print(f"[bot] Audit logging failed on message edit in guild {payload.guild_id}: {exc}")

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if payload.guild_id is None:
            return

        guild = self.get_guild(payload.guild_id)
        guild_name = guild.name if guild is not None else None
        cached_message = payload.cached_message

        try:
            await _handle_message_audit_event(
                guild=guild,
                guild_id=payload.guild_id,
                guild_name=guild_name,
                event_type="delete",
                channel_discord_id=str(payload.channel_id) if payload.channel_id else None,
                message_id=str(payload.message_id),
                author_discord_id=str(cached_message.author.id) if cached_message is not None else None,
                old_content=cached_message.content if cached_message is not None else None,
                new_content=None,
                is_author_bot=bool(cached_message.author.bot) if cached_message is not None else False,
            )
        except SQLAlchemyError as exc:
            print(f"[bot] Audit logging failed on message delete in guild {payload.guild_id}: {exc}")

    async def verification_sync_worker(self) -> None:
        while not self.is_closed():
            try:
                pending = _get_pending_sync_requests()
                for request in pending:
                    await self.process_sync_request(request)
            except Exception as exc:  # noqa: BLE001
                print(f"[bot] Verification sync worker error: {exc}")

            await asyncio.sleep(5)

    async def process_sync_request(self, request: dict) -> None:
        request_id = int(request["id"])
        guild_row_id = int(request["guild_id"])
        discord_guild_id = str(request["discord_guild_id"])

        _set_sync_request_status(request_id, "running")

        try:
            guild = self.get_guild(int(discord_guild_id))
            if guild is None:
                guild = await self.fetch_guild(int(discord_guild_id))

            summary = await run_verification_role_sync(guild, guild_row_id)
            _set_sync_request_status(request_id, "completed", summary=summary)
            print(f"[bot] Verification sync completed for guild {guild.id}: {summary}")
        except Exception as exc:  # noqa: BLE001
            _set_sync_request_status(request_id, "failed", error_text=str(exc))
            print(f"[bot] Verification sync failed for guild {discord_guild_id}: {exc}")


bot = Stage7Bot()


class VerifyEmailModal(discord.ui.Modal, title="Verify Email"):
    email = discord.ui.TextInput(
        label="Registered email",
        placeholder="name@example.com",
        required=True,
        max_length=320,
    )

    def __init__(self, guild: discord.Guild, member: discord.Member) -> None:
        super().__init__(timeout=180)
        self.guild = guild
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        config = _get_verification_config(str(self.guild.id))
        if not config["enabled"]:
            await interaction.response.send_message(
                "Verification module is disabled for this guild.",
                ephemeral=True,
            )
            return

        normalized_email = _normalize_email(str(self.email))
        if not _is_valid_email(normalized_email):
            await interaction.response.send_message("Please provide a valid email address.", ephemeral=True)
            return

        if not _email_is_registered(str(self.guild.id), normalized_email):
            await interaction.response.send_message(
                "Email not found in the registered member list. Contact an admin.",
                ephemeral=True,
            )
            return

        missing_roles = []
        added_count = 0
        errors = 0

        for role_id in config["role_ids"]:
            role = self.guild.get_role(role_id)
            if role is None:
                missing_roles.append(str(role_id))
                continue

            if role in self.member.roles:
                continue

            try:
                await self.member.add_roles(role, reason="Email verification")
                added_count += 1
            except discord.Forbidden as exc:
                errors += 1
                print(f"[bot] Failed to assign role {role_id} to user {self.member.id}: {exc}")
            except discord.HTTPException as exc:
                errors += 1
                print(f"[bot] Role assignment HTTP error for role {role_id} user {self.member.id}: {exc}")

        try:
            _upsert_verification_link(
                discord_guild_id=str(self.guild.id),
                guild_name=self.guild.name,
                member_discord_id=str(self.member.id),
                email=normalized_email,
            )
        except SQLAlchemyError as exc:
            print(f"[bot] Failed to store verification link for user {self.member.id}: {exc}")

        parts = ["Verification successful.", f"Roles added: {added_count}"]
        if missing_roles:
            parts.append(f"Missing role IDs in guild: {', '.join(missing_roles)}")
        if errors:
            parts.append("Some roles could not be assigned due to permission/hierarchy issues.")

        await interaction.response.send_message("\n".join(parts), ephemeral=True)


def get_module_settings_for_guild(discord_guild_id: str) -> dict[str, bool]:
    query = text(
        """
        SELECT
            COALESCE(w.enabled, 0) AS welcome_enabled,
            COALESCE(l.enabled, 0) AS leave_enabled,
            COALESCE(v.enabled, 0) AS verification_enabled,
            COALESCE(a.enabled, 0) AS audit_enabled,
            COALESCE(ac.enabled, 0) AS announcement_enabled
        FROM guilds g
        LEFT JOIN welcome_configs w ON w.guild_id = g.id
        LEFT JOIN leave_configs l ON l.guild_id = g.id
        LEFT JOIN verification_configs v ON v.guild_id = g.id
        LEFT JOIN audit_log_configs a ON a.guild_id = g.id
        LEFT JOIN announcement_configs ac ON ac.guild_id = g.id
        WHERE g.discord_guild_id = :discord_guild_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query, {"discord_guild_id": discord_guild_id}).mappings().first()

    if not row:
        return {
            "welcome": False,
            "leave": False,
            "verification": False,
            "audit": False,
            "announcement": False,
        }

    return {
        "welcome": bool(row["welcome_enabled"]),
        "leave": bool(row["leave_enabled"]),
        "verification": bool(row["verification_enabled"]),
        "audit": bool(row["audit_enabled"]),
        "announcement": bool(row["announcement_enabled"]),
    }


def get_dm_config_for_guild(discord_guild_id: str, event_type: str) -> dict:
    if event_type not in {"welcome", "leave"}:
        raise ValueError("event_type must be 'welcome' or 'leave'")

    table_name = "welcome_configs" if event_type == "welcome" else "leave_configs"
    query = text(
        f"""
        SELECT
            COALESCE(cfg.enabled, 0) AS enabled,
            cfg.markdown_text AS markdown_text,
            cfg.image_urls AS image_urls
        FROM guilds g
        LEFT JOIN {table_name} cfg ON cfg.guild_id = g.id
        WHERE g.discord_guild_id = :discord_guild_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(query, {"discord_guild_id": discord_guild_id}).mappings().first()

    if not row:
        return {"enabled": False, "markdown_text": None, "image_urls": []}

    return {
        "enabled": bool(row["enabled"]),
        "markdown_text": row["markdown_text"],
        "image_urls": _parse_json_list(row["image_urls"]),
    }


async def send_configured_dm(member: discord.Member, event_type: str) -> None:
    config = get_dm_config_for_guild(str(member.guild.id), event_type)
    if not config["enabled"]:
        return

    content = config.get("markdown_text") or None

    # Stage 6 image method: image URL list from config sent as embeds.
    embeds = []
    for image_url in (config.get("image_urls") or [])[:10]:
        embed = discord.Embed()
        embed.set_image(url=image_url)
        embeds.append(embed)

    if content is None and not embeds:
        print(f"[bot] {event_type} DM enabled but no content/images configured for guild {member.guild.id}")
        return

    try:
        await member.send(content=content, embeds=embeds)
        print(f"[bot] Sent {event_type} DM to user {member.id} in guild {member.guild.id}")
    except discord.Forbidden:
        print(f"[bot] Could not send {event_type} DM to user {member.id}: DMs closed or blocked")
    except discord.HTTPException as exc:
        print(f"[bot] Failed to send {event_type} DM to user {member.id}: {exc}")


async def run_verification_role_sync(guild: discord.Guild, guild_row_id: int) -> dict:
    data = _get_sync_data_for_guild(guild_row_id)
    role_ids = data["role_ids"]

    summary = {
        "guild_id": str(guild.id),
        "added": 0,
        "removed": 0,
        "skipped": 0,
        "errors": 0,
    }

    if not data["enabled"]:
        summary["skipped"] += 1
        summary["note"] = "verification module disabled"
        return summary

    if not role_ids:
        summary["skipped"] += 1
        summary["note"] = "no verification roles configured"
        return summary

    role_objects = [guild.get_role(role_id) for role_id in role_ids]
    role_objects = [role for role in role_objects if role is not None]
    if not role_objects:
        summary["skipped"] += 1
        summary["note"] = "configured roles not found in guild"
        return summary

    try:
        members = [member async for member in guild.fetch_members(limit=None)]
    except discord.Forbidden:
        members = list(guild.members)

    for member in members:
        if member.bot:
            continue

        registered = _member_is_registered(member.id, data["links"], data["valid_emails"])

        try:
            for role in role_objects:
                has_role = role in member.roles

                if registered and not has_role:
                    await member.add_roles(role, reason="Verification sync")
                    summary["added"] += 1
                elif (not registered) and data["remove_roles_when_unlisted"] and has_role:
                    await member.remove_roles(role, reason="Verification sync")
                    summary["removed"] += 1
        except discord.Forbidden:
            summary["errors"] += 1
        except discord.HTTPException:
            summary["errors"] += 1

        await asyncio.sleep(0.2)

    return summary


@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction) -> None:
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency_ms}ms")


@bot.tree.command(name="help", description="List available commands")
async def help_command(interaction: discord.Interaction) -> None:
    lines = [
        "**Available commands**",
        "`/ping` - Check bot latency",
        "`/help` - List available commands",
        "`/uptime` - Show bot uptime",
        "`/verify` - Verify with your email",
        "`/add-members-list` - Import verification email list (admin only)",
    ]

    if interaction.guild_id is not None:
        try:
            settings = get_module_settings_for_guild(str(interaction.guild_id))
            enabled = [name for name, value in settings.items() if value]
            enabled_text = ", ".join(enabled) if enabled else "none"
            lines.append(f"Enabled modules for this guild (DB): {enabled_text}")
        except SQLAlchemyError as exc:
            lines.append(f"Module settings read failed: {exc}")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@bot.tree.command(name="uptime", description="Show process uptime")
async def uptime(interaction: discord.Interaction) -> None:
    elapsed = datetime.now(UTC) - start_time
    total_seconds = int(elapsed.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f"Uptime: {hours}h {minutes}m {seconds}s")


@bot.tree.command(name="verify", description="Verify your email to receive configured roles")
async def verify(interaction: discord.Interaction) -> None:
    if interaction.guild is None or interaction.user is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    config = _get_verification_config(str(interaction.guild.id))
    if not config["enabled"]:
        await interaction.response.send_message("Verification module is disabled for this guild.", ephemeral=True)
        return

    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if member is None:
        await interaction.response.send_message("Could not resolve your member data in this guild.", ephemeral=True)
        return

    await interaction.response.send_modal(VerifyEmailModal(interaction.guild, member))


@bot.tree.command(name="add-members-list", description="Import registered emails from a text file")
@discord.app_commands.describe(file="Text file attachment with one email per line")
async def add_members_list(interaction: discord.Interaction, file: discord.Attachment) -> None:
    if interaction.guild is None or interaction.user is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if member is None:
        await interaction.response.send_message("Could not resolve your member data in this guild.", ephemeral=True)
        return

    if not (member.guild_permissions.administrator or member.guild_permissions.manage_guild):
        await interaction.response.send_message("You need Admin or Manage Guild permissions.", ephemeral=True)
        return

    config = _get_verification_config(str(interaction.guild.id))
    if not config["enabled"]:
        await interaction.response.send_message("Verification module is disabled for this guild.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        content = await file.read()
    except discord.HTTPException as exc:
        await interaction.followup.send(f"Failed to read attachment: {exc}", ephemeral=True)
        return

    if not content:
        await interaction.followup.send("The uploaded file is empty.", ephemeral=True)
        return

    decoded_text = content.decode("utf-8", errors="ignore")
    emails = _parse_emails_from_text(decoded_text)
    if not emails:
        await interaction.followup.send("No valid emails found in the uploaded file.", ephemeral=True)
        return

    file_hash = hashlib.sha256(content).hexdigest()

    try:
        guild_row_id = _import_registered_emails(
            discord_guild_id=str(interaction.guild.id),
            guild_name=interaction.guild.name,
            filename=file.filename or "members.txt",
            file_hash=file_hash,
            emails=emails,
        )

        request_id = _create_sync_request(
            guild_row_id=guild_row_id,
            source="bot_command_upload",
            requested_by_member_discord_id=str(member.id),
        )

        await bot.process_sync_request(
            {
                "id": request_id,
                "guild_id": guild_row_id,
                "discord_guild_id": str(interaction.guild.id),
            }
        )

        await interaction.followup.send(
            f"Imported {len(emails)} emails and started verification role sync.",
            ephemeral=True,
        )
    except SQLAlchemyError as exc:
        await interaction.followup.send(f"Failed to import list: {exc}", ephemeral=True)


async def main() -> None:
    configure_logging()
    db_startup_ping()

    token = DISCORD_BOT_TOKEN.strip()
    if not token or token == "replace_me":
        print("[bot] DISCORD_BOT_TOKEN not configured. Bot login skipped; keeping container alive for diagnostics.")
        while True:
            await asyncio.sleep(60)

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())

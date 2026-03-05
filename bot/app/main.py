import asyncio
import json
import os
from datetime import UTC, datetime

import discord
from discord.ext import commands
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_TEST_GUILD_ID = os.getenv("DISCORD_TEST_GUILD_ID", "").strip()

start_time = datetime.now(UTC)


def create_db_engine():
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, future=True, pool_pre_ping=True, connect_args=connect_args)


engine = create_db_engine()


def db_startup_ping() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("[bot] DB startup ping: OK")
        return True
    except SQLAlchemyError as exc:
        print(f"[bot] DB startup ping failed: {exc}")
        return False


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


def _parse_image_urls(raw_value) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(url).strip() for url in raw_value if str(url).strip()]
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                return [str(url).strip() for url in parsed if str(url).strip()]
        except json.JSONDecodeError:
            return []
    return []


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
        "image_urls": _parse_image_urls(row["image_urls"]),
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


class Stage6Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        if DISCORD_TEST_GUILD_ID:
            guild_obj = discord.Object(id=int(DISCORD_TEST_GUILD_ID))
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print(f"[bot] Synced slash commands to test guild {DISCORD_TEST_GUILD_ID}")
        else:
            await self.tree.sync()
            print("[bot] Synced global slash commands")

    async def on_ready(self) -> None:
        print(f"[bot] Logged in as {self.user} (id={self.user.id if self.user else 'n/a'})")

    async def on_member_join(self, member: discord.Member) -> None:
        try:
            await send_configured_dm(member, "welcome")
        except SQLAlchemyError as exc:
            print(f"[bot] Welcome config DB read failed for guild {member.guild.id}: {exc}")

    async def on_member_remove(self, member: discord.Member) -> None:
        try:
            await send_configured_dm(member, "leave")
        except SQLAlchemyError as exc:
            print(f"[bot] Leave config DB read failed for guild {member.guild.id}: {exc}")


bot = Stage6Bot()


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


async def main() -> None:
    db_startup_ping()

    token = DISCORD_BOT_TOKEN.strip()
    if not token or token == "replace_me":
        print("[bot] DISCORD_BOT_TOKEN not configured. Bot login skipped; keeping container alive for diagnostics.")
        while True:
            await asyncio.sleep(60)

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())

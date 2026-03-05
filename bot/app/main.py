import asyncio
import os
from datetime import UTC, datetime

import discord
from discord import app_commands
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


class Stage5Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

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


bot = Stage5Bot()


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
    await interaction.response.send_message(
        f"Uptime: {hours}h {minutes}m {seconds}s"
    )


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

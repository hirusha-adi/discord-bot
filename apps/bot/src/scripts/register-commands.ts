import "dotenv/config";
import { REST, Routes } from "discord.js";
import { createDashboardAdminCommand } from "../commands/slash/create-dashboard-admin.js";

const token = process.env.DISCORD_BOT_TOKEN;
const clientId = process.env.DISCORD_CLIENT_ID;
const guildId = process.env.DISCORD_GUILD_ID;

if (!token || !clientId || !guildId) {
    throw new Error(
        "Missing DISCORD_BOT_TOKEN, DISCORD_CLIENT_ID, or DISCORD_GUILD_ID",
    );
}

const commands = [createDashboardAdminCommand.data.toJSON()];
const rest = new REST({ version: "10" }).setToken(token);

async function registerGuildCommands() {
    await rest.put(Routes.applicationGuildCommands(clientId, guildId), {
        body: commands,
    });
    console.log("Registered guild slash commands.");
}

registerGuildCommands().catch((error) => {
    console.error("Failed to register slash commands", error);
    process.exit(1);
});

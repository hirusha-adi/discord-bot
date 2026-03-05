import { Client, GatewayIntentBits } from "discord.js";
import { env } from "./core/env.js";
import { interactionCreateEvent } from "./events/interactionCreate.js";

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

client.once("ready", () => {
    console.log(`Bot connected as ${client.user?.tag}`);
});

client.on(interactionCreateEvent.name, async (interaction) => {
    await interactionCreateEvent.execute(interaction);
});

client.login(env.discordToken).catch((error) => {
    console.error("Failed to start bot", error);
    process.exit(1);
});

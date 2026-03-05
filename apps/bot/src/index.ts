import { Client, GatewayIntentBits, Partials } from "discord.js";
import { env } from "./core/env.js";
import { botEvents } from "./events/index.js";
import { builtInModules } from "./modules/index.js";
import { ModuleManager } from "./core/module-manager.js";

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.GuildMessageReactions,
        GatewayIntentBits.GuildVoiceStates,
        GatewayIntentBits.DirectMessages,
        GatewayIntentBits.MessageContent,
    ],
    partials: [Partials.Channel, Partials.Message, Partials.Reaction, Partials.User],
});

const moduleManager = new ModuleManager(builtInModules);

client.once("ready", () => {
    console.log(`Bot connected as ${client.user?.tag}`);
    console.log(`Loaded modules: ${moduleManager.getAll().map((mod) => mod.key).join(", ")}`);
});

for (const eventDef of botEvents) {
    client.on(eventDef.name, async (...args) => {
        await eventDef.execute(...(args as never));
    });
}

client.login(env.discordToken).catch((error) => {
    console.error("Failed to start bot", error);
    process.exit(1);
});

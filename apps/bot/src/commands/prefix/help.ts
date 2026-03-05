import type { PrefixCommandDefinition } from "../../modules/types.js";

export const helpPrefixCommand: PrefixCommandDefinition = {
    name: "help",
    aliases: ["h", "commands"],
    cooldownSeconds: 3,
    async execute(message) {
        await message.reply([
            "Available commands:",
            "- !help: Show this help message.",
            "- !ping (alias: !p): Basic bot health check.",
            "- /help: Show slash-command help.",
            "- /create-dashboard-admin: Create dashboard credentials (admin only).",
        ].join("\n"));
    },
};

import type { PrefixCommandDefinition } from "../../modules/types.js";

export const pingPrefixCommand: PrefixCommandDefinition = {
    name: "ping",
    aliases: ["p"],
    cooldownSeconds: 5,
    async execute(message) {
        await message.reply("Pong.");
    },
};

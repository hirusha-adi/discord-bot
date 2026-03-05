import type { BotModule } from "../types.js";

export const moderationModule: BotModule = {
    key: "moderation",
    name: "Moderation",
    enabledByDefault: true,
    dashboardSchema: {
        actions: ["ban", "kick", "mute", "timeout", "warn", "softban", "unban"],
    },
};

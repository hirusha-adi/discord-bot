import type { BotModule } from "../types.js";

export const levelingModule: BotModule = {
    key: "leveling",
    name: "Leveling",
    enabledByDefault: true,
    dashboardSchema: {
        fields: ["xpPerMessage", "cooldownSeconds", "announcementChannelId"],
    },
};

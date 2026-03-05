import type { BotModule } from "../types.js";

export const loggingModule: BotModule = {
    key: "logging",
    name: "Logging",
    enabledByDefault: true,
    dashboardSchema: {
        eventChannels: true,
    },
};

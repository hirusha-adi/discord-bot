import type { BotModule } from "../types.js";

export const giveawaysModule: BotModule = {
    key: "giveaways",
    name: "Giveaways",
    enabledByDefault: true,
    dashboardSchema: {
        rerollEnabled: true,
        minDurationSeconds: 60,
    },
};

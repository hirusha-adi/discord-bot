import type { BotModule } from "../types.js";

export const economyModule: BotModule = {
    key: "economy",
    name: "Economy",
    enabledByDefault: true,
    dashboardSchema: {
        currencyName: "Coins",
        dailyReward: 100,
    },
};

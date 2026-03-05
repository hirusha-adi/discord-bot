import type { BotModule } from "../types.js";

export const automationModule: BotModule = {
    key: "automation",
    name: "Automation",
    enabledByDefault: true,
    dashboardSchema: {
        conditionActions: true,
    },
};

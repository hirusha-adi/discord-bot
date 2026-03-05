import type { BotModule } from "../types.js";

export const ticketsModule: BotModule = {
    key: "tickets",
    name: "Tickets",
    enabledByDefault: true,
    dashboardSchema: {
        defaultCategoryId: null,
        supportRoleIds: [],
    },
};

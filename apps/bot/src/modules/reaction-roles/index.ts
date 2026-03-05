import type { BotModule } from "../types.js";

export const reactionRolesModule: BotModule = {
    key: "reaction-roles",
    name: "Reaction Roles",
    enabledByDefault: true,
    dashboardSchema: {
        supports: ["message-reactions", "buttons", "select-menu"],
    },
};

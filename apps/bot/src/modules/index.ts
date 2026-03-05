import type { BotModule } from "./types.js";
import { moderationModule } from "./moderation/index.js";
import { levelingModule } from "./leveling/index.js";
import { reactionRolesModule } from "./reaction-roles/index.js";
import { loggingModule } from "./logging/index.js";
import { automationModule } from "./automation/index.js";
import { economyModule } from "./economy/index.js";
import { ticketsModule } from "./tickets/index.js";
import { giveawaysModule } from "./giveaways/index.js";

export const builtInModules: BotModule[] = [
    moderationModule,
    levelingModule,
    reactionRolesModule,
    loggingModule,
    automationModule,
    economyModule,
    ticketsModule,
    giveawaysModule,
];

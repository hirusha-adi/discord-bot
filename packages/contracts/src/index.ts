export const MODULE_KEYS = [
    "moderation",
    "leveling",
    "reaction-roles",
    "logging",
    "automation",
    "economy",
    "tickets",
    "giveaways",
] as const;

export type ModuleKey = (typeof MODULE_KEYS)[number];

export interface DashboardAdminClaims {
    dashboardAdminId: string;
    discordUserId: string;
    guildIds: string[];
}

export interface GuildModuleConfig<T = Record<string, unknown>> {
    moduleKey: ModuleKey;
    enabled: boolean;
    config: T;
}

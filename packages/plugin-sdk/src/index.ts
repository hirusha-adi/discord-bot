import type { ClientEvents, ChatInputCommandInteraction } from "discord.js";

export type ModuleEventHandler<K extends keyof ClientEvents = keyof ClientEvents> = {
    event: K;
    execute: (...args: ClientEvents[K]) => Promise<void> | void;
};

export interface ModuleCommand {
    name: string;
    execute: (interaction: ChatInputCommandInteraction) => Promise<void>;
}

export interface ModuleManifest {
    key: string;
    name: string;
    description: string;
    defaultEnabled: boolean;
    dashboardSchema: Record<string, unknown>;
}

export interface BotModule {
    manifest: ModuleManifest;
    commands: ModuleCommand[];
    eventHandlers: ModuleEventHandler[];
}

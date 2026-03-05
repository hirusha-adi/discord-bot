import type {
    ChatInputCommandInteraction,
    ClientEvents,
    Message,
} from "discord.js";

export interface SlashCommandDefinition {
    name: string;
    cooldownSeconds?: number;
    execute: (interaction: ChatInputCommandInteraction) => Promise<void>;
}

export interface PrefixCommandDefinition {
    name: string;
    aliases?: string[];
    cooldownSeconds?: number;
    execute: (message: Message, args: string[]) => Promise<void>;
}

export interface BotEventDefinition<K extends keyof ClientEvents = keyof ClientEvents> {
    event: K;
    execute: (...args: ClientEvents[K]) => Promise<void> | void;
}

export interface BotModule {
    key: string;
    name: string;
    enabledByDefault: boolean;
    dashboardSchema: Record<string, unknown>;
    slashCommands?: SlashCommandDefinition[];
    prefixCommands?: PrefixCommandDefinition[];
    events?: BotEventDefinition[];
}

import type {
    ChatInputCommandInteraction,
    Message,
} from "discord.js";
import { MessageFlags } from "discord.js";
import { createDashboardAdminCommand } from "../commands/slash/create-dashboard-admin.js";
import { helpSlashCommand } from "../commands/slash/help.js";
import { pingPrefixCommand } from "../commands/prefix/ping.js";
import { helpPrefixCommand } from "../commands/prefix/help.js";
import type { PrefixCommandDefinition, SlashCommandDefinition } from "../modules/types.js";
import { prisma } from "./prisma.js";

const slashCommands: SlashCommandDefinition[] = [
    {
        name: helpSlashCommand.data.name,
        cooldownSeconds: 3,
        execute: helpSlashCommand.execute,
    },
    {
        name: createDashboardAdminCommand.data.name,
        cooldownSeconds: 10,
        execute: createDashboardAdminCommand.execute,
    },
];

const prefixCommands: PrefixCommandDefinition[] = [helpPrefixCommand, pingPrefixCommand];

const slashCommandMap = new Map(slashCommands.map((command) => [command.name, command]));
const prefixCommandMap = new Map<string, PrefixCommandDefinition>();
for (const command of prefixCommands) {
    prefixCommandMap.set(command.name, command);
    for (const alias of command.aliases ?? []) {
        prefixCommandMap.set(alias, command);
    }
}

const cooldowns = new Map<string, number>();

function keyForCooldown(userId: string, commandName: string): string {
    return `${userId}:${commandName}`;
}

function isOnCooldown(userId: string, commandName: string, cooldownSeconds = 0): boolean {
    if (!cooldownSeconds) {
        return false;
    }

    const key = keyForCooldown(userId, commandName);
    const now = Date.now();
    const until = cooldowns.get(key) ?? 0;

    if (until > now) {
        return true;
    }

    cooldowns.set(key, now + cooldownSeconds * 1000);
    return false;
}

export async function handleSlashCommand(interaction: ChatInputCommandInteraction): Promise<void> {
    const command = slashCommandMap.get(interaction.commandName);
    if (!command) {
        return;
    }

    if (isOnCooldown(interaction.user.id, command.name, command.cooldownSeconds)) {
        const payload = {
            content: "This command is on cooldown. Try again in a moment.",
            flags: MessageFlags.Ephemeral,
        };

        if (interaction.deferred || interaction.replied) {
            await interaction.editReply(payload);
        } else {
            await interaction.reply(payload);
        }
        return;
    }

    await command.execute(interaction);

    if (interaction.guildId) {
        await prisma.auditLog.create({
            data: {
                guildId: interaction.guildId,
                actorType: "DISCORD_USER",
                actorId: interaction.user.id,
                action: `COMMAND_SLASH_${command.name.toUpperCase()}`,
                targetType: "Command",
                targetId: command.name,
            },
        });
    }
}

export async function handlePrefixCommand(message: Message): Promise<void> {
    if (!message.guildId || message.author.bot) {
        return;
    }

    const settings = await prisma.guildSettings.findUnique({ where: { guildId: message.guildId } });
    const prefix = settings?.prefix ?? "!";

    if (!message.content.startsWith(prefix)) {
        return;
    }

    const raw = message.content.slice(prefix.length).trim();
    if (!raw) {
        return;
    }

    const [commandName, ...args] = raw.split(/\s+/g);
    const command = prefixCommandMap.get(commandName.toLowerCase());
    if (!command) {
        return;
    }

    if (isOnCooldown(message.author.id, command.name, command.cooldownSeconds)) {
        await message.reply("That command is on cooldown.");
        return;
    }

    await command.execute(message, args);

    await prisma.auditLog.create({
        data: {
            guildId: message.guildId,
            actorType: "DISCORD_USER",
            actorId: message.author.id,
            action: `COMMAND_PREFIX_${command.name.toUpperCase()}`,
            targetType: "Command",
            targetId: command.name,
        },
    });
}

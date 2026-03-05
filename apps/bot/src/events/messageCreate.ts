import { Events, Message } from "discord.js";
import { handlePrefixCommand } from "../core/commands.js";
import { prisma } from "../core/prisma.js";

export const messageCreateEvent = {
    name: Events.MessageCreate,
    async execute(message: Message): Promise<void> {
        if (message.author.bot || !message.guildId) {
            return;
        }

        await handlePrefixCommand(message);

        // Minimal XP accrual baseline with per-message updates.
        await prisma.levelingData.upsert({
            where: {
                guildId_userId: {
                    guildId: message.guildId,
                    userId: message.author.id,
                },
            },
            update: {
                xp: { increment: 5 },
                messageCount: { increment: 1 },
                lastMessageAt: new Date(),
            },
            create: {
                guildId: message.guildId,
                userId: message.author.id,
                xp: 5,
                messageCount: 1,
                lastMessageAt: new Date(),
            },
        });
    },
};

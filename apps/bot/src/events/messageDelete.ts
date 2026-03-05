import { Events, Message, PartialMessage } from "discord.js";
import { prisma } from "../core/prisma.js";

export const messageDeleteEvent = {
    name: Events.MessageDelete,
    async execute(message: Message | PartialMessage): Promise<void> {
        if (!message.guildId || !message.author?.id) {
            return;
        }

        await prisma.auditLog.create({
            data: {
                guildId: message.guildId,
                actorType: "DISCORD_USER",
                actorId: message.author.id,
                action: "MESSAGE_DELETE",
                targetType: "Message",
                targetId: message.id,
            },
        });
    },
};

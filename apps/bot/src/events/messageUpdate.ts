import { Events, Message, PartialMessage } from "discord.js";
import { prisma } from "../core/prisma.js";

export const messageUpdateEvent = {
    name: Events.MessageUpdate,
    async execute(oldMessage: Message | PartialMessage, newMessage: Message | PartialMessage): Promise<void> {
        if (!newMessage.guildId || !newMessage.author?.id) {
            return;
        }

        await prisma.auditLog.create({
            data: {
                guildId: newMessage.guildId,
                actorType: "DISCORD_USER",
                actorId: newMessage.author.id,
                action: "MESSAGE_UPDATE",
                targetType: "Message",
                targetId: newMessage.id,
                metadataJson: JSON.stringify({
                    oldContent: oldMessage.content ?? null,
                    newContent: newMessage.content ?? null,
                }),
            },
        });
    },
};

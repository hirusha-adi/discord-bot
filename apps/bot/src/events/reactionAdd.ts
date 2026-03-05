import { Events, MessageReaction, PartialMessageReaction, User, PartialUser } from "discord.js";
import { prisma } from "../core/prisma.js";

export const reactionAddEvent = {
    name: Events.MessageReactionAdd,
    async execute(reaction: MessageReaction | PartialMessageReaction, user: User | PartialUser): Promise<void> {
        const guildId = reaction.message.guildId;
        if (!guildId || !user.id) {
            return;
        }

        await prisma.auditLog.create({
            data: {
                guildId,
                actorType: "DISCORD_USER",
                actorId: user.id,
                action: "REACTION_ADD",
                targetType: "Message",
                targetId: reaction.message.id,
                metadataJson: JSON.stringify({ emoji: reaction.emoji.name }),
            },
        });
    },
};

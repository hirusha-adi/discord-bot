import { Events, Guild } from "discord.js";
import { prisma } from "../core/prisma.js";

export const guildUpdateEvent = {
    name: Events.GuildUpdate,
    async execute(oldGuild: Guild, newGuild: Guild): Promise<void> {
        await prisma.guild.upsert({
            where: { id: newGuild.id },
            update: {
                name: newGuild.name,
                ownerDiscordId: newGuild.ownerId,
            },
            create: {
                id: newGuild.id,
                name: newGuild.name,
                ownerDiscordId: newGuild.ownerId,
            },
        });

        await prisma.auditLog.create({
            data: {
                guildId: newGuild.id,
                actorType: "SYSTEM",
                actorId: "discord-gateway",
                action: "GUILD_UPDATE",
                targetType: "Guild",
                targetId: newGuild.id,
                metadataJson: JSON.stringify({
                    oldName: oldGuild.name,
                    newName: newGuild.name,
                }),
            },
        });
    },
};

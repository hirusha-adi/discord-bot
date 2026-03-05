import { Events, GuildMember } from "discord.js";
import { prisma } from "../core/prisma.js";

export const guildMemberRemoveEvent = {
    name: Events.GuildMemberRemove,
    async execute(member: GuildMember): Promise<void> {
        await prisma.auditLog.create({
            data: {
                guildId: member.guild.id,
                actorType: "DISCORD_USER",
                actorId: member.id,
                action: "GUILD_MEMBER_REMOVE",
                targetType: "Member",
                targetId: member.id,
            },
        });
    },
};

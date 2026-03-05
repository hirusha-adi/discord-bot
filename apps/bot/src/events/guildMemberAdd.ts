import { Events, GuildMember } from "discord.js";
import { prisma } from "../core/prisma.js";

export const guildMemberAddEvent = {
    name: Events.GuildMemberAdd,
    async execute(member: GuildMember): Promise<void> {
        await prisma.user.upsert({
            where: { id: member.user.id },
            update: {
                username: member.user.username,
                avatarUrl: member.user.displayAvatarURL(),
                lastSeenAt: new Date(),
            },
            create: {
                id: member.user.id,
                username: member.user.username,
                avatarUrl: member.user.displayAvatarURL(),
                lastSeenAt: new Date(),
            },
        });

        await prisma.auditLog.create({
            data: {
                guildId: member.guild.id,
                actorType: "DISCORD_USER",
                actorId: member.user.id,
                action: "GUILD_MEMBER_ADD",
                targetType: "Member",
                targetId: member.id,
            },
        });
    },
};

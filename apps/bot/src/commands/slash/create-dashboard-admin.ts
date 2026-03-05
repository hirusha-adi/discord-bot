import {
    ChatInputCommandInteraction,
    PermissionFlagsBits,
    SlashCommandBuilder,
} from "discord.js";
import type { Prisma } from "@prisma/client";
import { prisma } from "../../core/prisma.js";
import { generateSecurePassword, hashPassword } from "../../core/password.js";

export const createDashboardAdminCommand = {
    data: new SlashCommandBuilder()
        .setName("create-dashboard-admin")
        .setDescription("Create dashboard credentials for this server admin."),

    async execute(interaction: ChatInputCommandInteraction): Promise<void> {
        if (!interaction.inGuild() || !interaction.guildId || !interaction.guild) {
            await interaction.reply({
                content: "This command can only be used inside a server.",
                ephemeral: true,
            });
            return;
        }

        const hasAdminPerm = interaction.memberPermissions?.has(
            PermissionFlagsBits.Administrator,
        );

        if (!hasAdminPerm) {
            await interaction.reply({
                content: "You must have Administrator permission to run this command.",
                ephemeral: true,
            });
            return;
        }

        await interaction.deferReply({ ephemeral: true });

        const guildId = interaction.guildId;
        const discordUserId = interaction.user.id;

        await prisma.guild.upsert({
            where: { id: guildId },
            update: {
                name: interaction.guild.name,
            },
            create: {
                id: guildId,
                name: interaction.guild.name,
                ownerDiscordId: interaction.guild.ownerId,
            },
        });

        await prisma.user.upsert({
            where: { id: discordUserId },
            update: {
                username: interaction.user.username,
                avatarUrl: interaction.user.displayAvatarURL(),
                lastSeenAt: new Date(),
            },
            create: {
                id: discordUserId,
                username: interaction.user.username,
                avatarUrl: interaction.user.displayAvatarURL(),
                lastSeenAt: new Date(),
            },
        });

        const existing = await prisma.dashboardAdmin.findUnique({
            where: {
                discordUserId_guildId: {
                    discordUserId,
                    guildId,
                },
            },
        });

        if (existing) {
            await interaction.editReply(
                "You already have dashboard credentials for this server. Please contact support if you need a reset.",
            );
            return;
        }

        const username = `u_${discordUserId}`;
        const plainPassword = generateSecurePassword(18);
        const passwordHash = await hashPassword(plainPassword);

        const createdAdmin = await prisma.$transaction(async (tx: Prisma.TransactionClient) => {
            const admin = await tx.dashboardAdmin.create({
                data: {
                    discordUserId,
                    guildId,
                    username,
                    passwordHash,
                },
            });

            await tx.auditLog.create({
                data: {
                    guildId,
                    actorType: "DISCORD_USER",
                    actorId: discordUserId,
                    action: "DASHBOARD_ADMIN_CREATED",
                    targetType: "DashboardAdmin",
                    targetId: admin.id,
                    metadataJson: JSON.stringify({
                        discordUserId,
                        username,
                        guildId,
                    }),
                },
            });

            return admin;
        });

        try {
            await interaction.user.send([
                "Your dashboard account has been created.",
                `Guild: ${interaction.guild.name} (${guildId})`,
                `User ID: ${discordUserId}`,
                `Username: ${username}`,
                `Password: ${plainPassword}`,
                "",
                "For security, change this password immediately after your first login.",
            ].join("\n"));

            await interaction.editReply(
                "Dashboard credentials were created and sent to your DMs.",
            );
        } catch {
            await prisma.$transaction(async (tx: Prisma.TransactionClient) => {
                await tx.dashboardAdmin.delete({
                    where: { id: createdAdmin.id },
                });

                await tx.auditLog.create({
                    data: {
                        guildId,
                        actorType: "DISCORD_USER",
                        actorId: discordUserId,
                        action: "DASHBOARD_ADMIN_CREATE_FAILED_DM",
                        targetType: "DashboardAdmin",
                        targetId: createdAdmin.id,
                        metadataJson: JSON.stringify({
                            discordUserId,
                            username,
                            guildId,
                        }),
                    },
                });
            });

            await interaction.editReply(
                "I could not DM you. Please enable direct messages from server members, then run the command again.",
            );
        }
    },
};

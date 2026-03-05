import type { FastifyInstance } from "fastify";
import { prisma } from "../../db.js";
import { requireAuth, requireGuildAccess } from "../../middleware/auth.js";

export async function registerGuildRoutes(app: FastifyInstance): Promise<void> {
    app.get("/guilds", { preHandler: [requireAuth] }, async (request, reply) => {
        const admins = await prisma.dashboardAdmin.findMany({
            where: {
                discordUserId: request.auth!.discordUserId,
                isActive: true,
            },
            include: {
                guild: true,
            },
            orderBy: {
                createdAt: "desc",
            },
        });

        reply.send({
            guilds: admins.map((item) => ({
                guildId: item.guildId,
                name: item.guild.name,
                ownerDiscordId: item.guild.ownerDiscordId,
            })),
        });
    });

    app.get("/guilds/:guildId", { preHandler: [requireAuth, requireGuildAccess] }, async (request, reply) => {
        const { guildId } = request.params as { guildId: string };

        const [guild, settings, modules] = await Promise.all([
            prisma.guild.findUnique({ where: { id: guildId } }),
            prisma.guildSettings.findUnique({ where: { guildId } }),
            prisma.guildModule.findMany({ where: { guildId }, orderBy: { moduleKey: "asc" } }),
        ]);

        if (!guild) {
            reply.status(404).send({ error: "GUILD_NOT_FOUND" });
            return;
        }

        reply.send({ guild, settings, modules });
    });
}

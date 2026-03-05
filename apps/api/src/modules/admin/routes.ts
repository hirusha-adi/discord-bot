import type { FastifyInstance } from "fastify";
import { config } from "../../config.js";
import { prisma } from "../../db.js";
import { requireAuth } from "../../middleware/auth.js";

export async function registerOwnerAdminRoutes(app: FastifyInstance): Promise<void> {
    app.get("/admin/guilds", { preHandler: [requireAuth] }, async (request, reply) => {
        if (!config.ownerDiscordUserIds.includes(request.auth!.discordUserId)) {
            reply.status(403).send({ error: "OWNER_ONLY" });
            return;
        }

        const guilds = await prisma.guild.findMany({
            orderBy: { createdAt: "desc" },
            include: {
                _count: {
                    select: {
                        dashboardAdmins: true,
                        modules: true,
                    },
                },
            },
        });

        reply.send({ guilds });
    });

    app.get("/admin/metrics", { preHandler: [requireAuth] }, async (request, reply) => {
        if (!config.ownerDiscordUserIds.includes(request.auth!.discordUserId)) {
            reply.status(403).send({ error: "OWNER_ONLY" });
            return;
        }

        const [guildCount, adminCount, sessionCount, auditCount] = await Promise.all([
            prisma.guild.count(),
            prisma.dashboardAdmin.count({ where: { isActive: true } }),
            prisma.adminSession.count({ where: { revokedAt: null, expiresAt: { gt: new Date() } } }),
            prisma.auditLog.count(),
        ]);

        reply.send({ guildCount, adminCount, sessionCount, auditCount });
    });
}

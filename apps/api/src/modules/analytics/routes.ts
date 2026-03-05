import type { FastifyInstance } from "fastify";
import { prisma } from "../../db.js";
import { requireAuth, requireGuildAccess } from "../../middleware/auth.js";

export async function registerAnalyticsRoutes(app: FastifyInstance): Promise<void> {
    app.get("/guilds/:guildId/analytics/summary", { preHandler: [requireAuth, requireGuildAccess] }, async (request, reply) => {
        const { guildId } = request.params as { guildId: string };

        const [membersTracked, commandUsage, moderationActions, ticketsOpen] = await Promise.all([
            prisma.levelingData.count({ where: { guildId } }),
            prisma.auditLog.count({
                where: {
                    guildId,
                    action: { startsWith: "COMMAND_" },
                },
            }),
            prisma.moderationLog.count({ where: { guildId } }),
            prisma.ticket.count({ where: { guildId, status: "OPEN" } }),
        ]);

        reply.send({
            membersTracked,
            commandUsage,
            moderationActions,
            ticketsOpen,
        });
    });
}

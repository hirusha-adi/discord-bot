import type { FastifyReply, FastifyRequest } from "fastify";
import { hashSessionToken } from "../lib/security.js";
import { config } from "../config.js";
import { prisma } from "../db.js";
import type { AuthContext } from "../types.js";

declare module "fastify" {
    interface FastifyRequest {
        auth?: AuthContext;
    }
}

export async function requireAuth(request: FastifyRequest, reply: FastifyReply): Promise<void> {
    const rawToken = request.cookies[config.sessionCookieName];
    if (!rawToken) {
        reply.status(401).send({ error: "UNAUTHENTICATED" });
        return;
    }

    const tokenHash = hashSessionToken(rawToken);
    const session = await prisma.adminSession.findFirst({
        where: {
            tokenHash,
            revokedAt: null,
            expiresAt: { gt: new Date() },
        },
        include: {
            admin: true,
        },
    });

    if (!session || !session.admin.isActive) {
        reply.status(401).send({ error: "INVALID_SESSION" });
        return;
    }

    request.auth = {
        dashboardAdminId: session.dashboardAdminId,
        discordUserId: session.admin.discordUserId,
        guildId: session.admin.guildId,
    };
}

export async function requireGuildAccess(request: FastifyRequest, reply: FastifyReply): Promise<void> {
    if (!request.auth) {
        reply.status(401).send({ error: "UNAUTHENTICATED" });
        return;
    }

    const guildId = (request.params as { guildId?: string }).guildId;
    if (!guildId) {
        reply.status(400).send({ error: "MISSING_GUILD_ID" });
        return;
    }

    if (guildId !== request.auth.guildId) {
        reply.status(403).send({ error: "GUILD_ACCESS_DENIED" });
        return;
    }
}

import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { config } from "../../config.js";
import { prisma } from "../../db.js";
import { createSessionToken, hashSessionToken, verifyPassword } from "../../lib/security.js";
import { requireAuth } from "../../middleware/auth.js";

const loginSchema = z.object({
    userId: z.string().min(5),
    password: z.string().min(8),
    guildId: z.string().min(5),
});

export async function registerAuthRoutes(app: FastifyInstance): Promise<void> {
    app.post("/auth/login", async (request, reply) => {
        const parsed = loginSchema.safeParse(request.body);
        if (!parsed.success) {
            reply.status(400).send({ error: "INVALID_PAYLOAD" });
            return;
        }

        const { userId, password, guildId } = parsed.data;

        const admin = await prisma.dashboardAdmin.findUnique({
            where: {
                discordUserId_guildId: {
                    discordUserId: userId,
                    guildId,
                },
            },
        });

        if (!admin || !admin.isActive) {
            reply.status(401).send({ error: "INVALID_CREDENTIALS" });
            return;
        }

        const valid = await verifyPassword(admin.passwordHash, password);
        if (!valid) {
            reply.status(401).send({ error: "INVALID_CREDENTIALS" });
            return;
        }

        const rawToken = createSessionToken();
        const tokenHash = hashSessionToken(rawToken);
        const expiresAt = new Date(Date.now() + config.sessionTtlHours * 60 * 60 * 1000);

        await prisma.$transaction(async (tx) => {
            await tx.adminSession.create({
                data: {
                    dashboardAdminId: admin.id,
                    tokenHash,
                    ipAddress: request.ip,
                    userAgent: request.headers["user-agent"]?.toString(),
                    expiresAt,
                },
            });

            await tx.dashboardAdmin.update({
                where: { id: admin.id },
                data: { lastLogin: new Date() },
            });

            await tx.auditLog.create({
                data: {
                    guildId,
                    actorType: "DASHBOARD_ADMIN",
                    actorId: admin.discordUserId,
                    action: "DASHBOARD_LOGIN",
                    targetType: "DashboardAdmin",
                    targetId: admin.id,
                    metadataJson: JSON.stringify({ guildId }),
                    ipAddress: request.ip,
                    userAgent: request.headers["user-agent"]?.toString(),
                },
            });
        });

        reply.setCookie(config.sessionCookieName, rawToken, {
            httpOnly: true,
            secure: config.nodeEnv === "production",
            sameSite: "lax",
            path: "/",
            expires: expiresAt,
        });

        reply.send({
            ok: true,
            dashboardAdminId: admin.id,
            discordUserId: admin.discordUserId,
            guildId: admin.guildId,
        });
    });

    app.post("/auth/logout", { preHandler: [requireAuth] }, async (request, reply) => {
        const rawToken = request.cookies[config.sessionCookieName];
        if (rawToken) {
            await prisma.adminSession.updateMany({
                where: {
                    tokenHash: hashSessionToken(rawToken),
                    revokedAt: null,
                },
                data: { revokedAt: new Date() },
            });
        }

        reply.clearCookie(config.sessionCookieName, { path: "/" });
        reply.send({ ok: true });
    });

    app.get("/auth/me", { preHandler: [requireAuth] }, async (request, reply) => {
        reply.send({
            ok: true,
            auth: request.auth,
        });
    });
}

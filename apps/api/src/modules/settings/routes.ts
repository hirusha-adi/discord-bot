import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { prisma } from "../../db.js";
import { requireAuth, requireGuildAccess } from "../../middleware/auth.js";

const upsertSettingsSchema = z.object({
    prefix: z.string().min(1).max(5).optional(),
    locale: z.string().min(2).max(20).optional(),
    timezone: z.string().min(2).max(64).optional(),
    logChannelId: z.string().optional().nullable(),
    modLogChannelId: z.string().optional().nullable(),
    welcomeChannelId: z.string().optional().nullable(),
    goodbyeChannelId: z.string().optional().nullable(),
    dashboardTheme: z.string().optional().nullable(),
    antiSpamEnabled: z.boolean().optional(),
    antiInviteEnabled: z.boolean().optional(),
    antiCapsEnabled: z.boolean().optional(),
});

const moduleSchema = z.object({
    moduleKey: z.string().min(2),
    enabled: z.boolean(),
    configJson: z.string().optional().nullable(),
});

export async function registerSettingsRoutes(app: FastifyInstance): Promise<void> {
    app.put("/guilds/:guildId/settings", { preHandler: [requireAuth, requireGuildAccess] }, async (request, reply) => {
        const { guildId } = request.params as { guildId: string };
        const parsed = upsertSettingsSchema.safeParse(request.body);

        if (!parsed.success) {
            reply.status(400).send({ error: "INVALID_PAYLOAD" });
            return;
        }

        const settings = await prisma.guildSettings.upsert({
            where: { guildId },
            update: parsed.data,
            create: {
                guildId,
                ...parsed.data,
            },
        });

        await prisma.auditLog.create({
            data: {
                guildId,
                actorType: "DASHBOARD_ADMIN",
                actorId: request.auth!.discordUserId,
                action: "GUILD_SETTINGS_UPDATED",
                targetType: "GuildSettings",
                targetId: settings.id,
                metadataJson: JSON.stringify(parsed.data),
            },
        });

        reply.send({ ok: true, settings });
    });

    app.put("/guilds/:guildId/modules/:moduleKey", { preHandler: [requireAuth, requireGuildAccess] }, async (request, reply) => {
        const { guildId, moduleKey } = request.params as { guildId: string; moduleKey: string };
        const parsed = moduleSchema.safeParse({
            ...(request.body as object),
            moduleKey,
        });

        if (!parsed.success) {
            reply.status(400).send({ error: "INVALID_PAYLOAD" });
            return;
        }

        const moduleRecord = await prisma.guildModule.upsert({
            where: {
                guildId_moduleKey: { guildId, moduleKey },
            },
            update: {
                enabled: parsed.data.enabled,
                configJson: parsed.data.configJson ?? null,
            },
            create: {
                guildId,
                moduleKey,
                enabled: parsed.data.enabled,
                configJson: parsed.data.configJson ?? null,
            },
        });

        await prisma.auditLog.create({
            data: {
                guildId,
                actorType: "DASHBOARD_ADMIN",
                actorId: request.auth!.discordUserId,
                action: "GUILD_MODULE_UPDATED",
                targetType: "GuildModule",
                targetId: moduleRecord.id,
                metadataJson: JSON.stringify({
                    moduleKey,
                    enabled: moduleRecord.enabled,
                }),
            },
        });

        reply.send({ ok: true, module: moduleRecord });
    });
}

import cookie from "@fastify/cookie";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import type { FastifyInstance } from "fastify";
import { config } from "../config.js";

export async function registerSecurityPlugins(app: FastifyInstance): Promise<void> {
    await app.register(cors, {
        origin: true,
        credentials: true,
    });

    await app.register(cookie, {
        parseOptions: {},
    });

    await app.register(rateLimit, {
        max: 120,
        timeWindow: "1 minute",
        keyGenerator: (request) => request.ip,
    });

    app.addHook("onRequest", async (request, reply) => {
        reply.header("X-Frame-Options", "DENY");
        reply.header("X-Content-Type-Options", "nosniff");
        reply.header("Referrer-Policy", "no-referrer");
        if (config.nodeEnv === "production") {
            reply.header("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload");
        }
    });
}

import Fastify from "fastify";
import { registerSecurityPlugins } from "./plugins/security.js";
import { registerAuthRoutes } from "./modules/auth/routes.js";
import { registerGuildRoutes } from "./modules/guilds/routes.js";
import { registerSettingsRoutes } from "./modules/settings/routes.js";
import { registerAnalyticsRoutes } from "./modules/analytics/routes.js";
import { registerOwnerAdminRoutes } from "./modules/admin/routes.js";

export async function buildApiApp() {
    const app = Fastify({ logger: true });

    await registerSecurityPlugins(app);

    app.get("/health", async () => ({ ok: true }));

    await registerAuthRoutes(app);
    await registerGuildRoutes(app);
    await registerSettingsRoutes(app);
    await registerAnalyticsRoutes(app);
    await registerOwnerAdminRoutes(app);

    return app;
}

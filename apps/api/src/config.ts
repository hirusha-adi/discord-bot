import { loadApiEnvironment } from "./load-env.js";

loadApiEnvironment();

function required(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required env var: ${name}`);
    }
    return value;
}

export const config = {
    nodeEnv: process.env.NODE_ENV ?? "development",
    port: Number(process.env.API_PORT ?? 3001),
    host: process.env.API_HOST ?? "0.0.0.0",
    databaseUrl: required("DATABASE_URL"),
    sessionCookieName: process.env.SESSION_COOKIE_NAME ?? "dashboard_session",
    sessionTtlHours: Number(process.env.SESSION_TTL_HOURS ?? 24),
    ownerDiscordUserIds: (process.env.OWNER_DISCORD_USER_IDS ?? "")
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
};

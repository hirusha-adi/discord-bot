import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

let loaded = false;

export function loadApiEnvironment(): void {
    if (loaded) {
        return;
    }

    // Prefer the repository root .env when scripts run from apps/api.
    const here = fileURLToPath(new URL(".", import.meta.url));
    const rootDir = resolve(here, "../../../");
    const rootEnvPath = resolve(here, "../../../.env");

    if (existsSync(rootEnvPath)) {
        dotenv.config({ path: rootEnvPath });
    } else {
        dotenv.config();
    }

    const databaseUrl = process.env.DATABASE_URL;
    if (databaseUrl?.startsWith("file:./") || databaseUrl?.startsWith("file:../")) {
        const relativeDbPath = databaseUrl.slice("file:".length);
        const absoluteDbPath = resolve(rootDir, relativeDbPath);
        mkdirSync(dirname(absoluteDbPath), { recursive: true });
        process.env.DATABASE_URL = `file:${absoluteDbPath.replace(/\\/g, "/")}`;
    }

    loaded = true;
}

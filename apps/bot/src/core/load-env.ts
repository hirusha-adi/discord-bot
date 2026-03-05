import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

let loaded = false;

export function loadBotEnvironment(): void {
    if (loaded) {
        return;
    }

    // Always prefer repo-root .env so filtered pnpm commands work from apps/bot.
    const here = fileURLToPath(new URL(".", import.meta.url));
    const rootEnvPath = resolve(here, "../../../../.env");

    if (existsSync(rootEnvPath)) {
        dotenv.config({ path: rootEnvPath });
    } else {
        dotenv.config();
    }

    loaded = true;
}

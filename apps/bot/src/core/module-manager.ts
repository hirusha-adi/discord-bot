import { prisma } from "./prisma.js";
import type { BotModule } from "../modules/types.js";

export class ModuleManager {
    constructor(private readonly modules: BotModule[]) { }

    getAll(): BotModule[] {
        return this.modules;
    }

    async isEnabled(guildId: string, moduleKey: string, defaultEnabled: boolean): Promise<boolean> {
        const moduleConfig = await prisma.guildModule.findUnique({
            where: {
                guildId_moduleKey: { guildId, moduleKey },
            },
        });

        if (!moduleConfig) {
            return defaultEnabled;
        }

        return moduleConfig.enabled;
    }
}

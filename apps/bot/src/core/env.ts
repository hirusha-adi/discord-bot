import "dotenv/config";

function requireEnv(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}

export const env = {
    discordToken: requireEnv("DISCORD_BOT_TOKEN"),
    databaseUrl: requireEnv("DATABASE_URL"),
};

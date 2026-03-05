import {
    ChatInputCommandInteraction,
    MessageFlags,
    SlashCommandBuilder,
} from "discord.js";

export const helpSlashCommand = {
    data: new SlashCommandBuilder()
        .setName("help")
        .setDescription("Show available bot commands and quick usage."),

    async execute(interaction: ChatInputCommandInteraction): Promise<void> {
        await interaction.reply({
            content: [
                "Available commands:",
                "- /help: Show this help message.",
                "- /create-dashboard-admin: Create dashboard credentials (admin only).",
                "- !help: Show prefix command help.",
                "- !ping (alias: !p): Basic bot health check.",
            ].join("\n"),
            flags: MessageFlags.Ephemeral,
        });
    },
};

import { Events, Interaction } from "discord.js";
import { createDashboardAdminCommand } from "../commands/slash/create-dashboard-admin.js";

const commandRegistry = new Map([
    [createDashboardAdminCommand.data.name, createDashboardAdminCommand],
]);

export const interactionCreateEvent = {
    name: Events.InteractionCreate,
    async execute(interaction: Interaction): Promise<void> {
        if (!interaction.isChatInputCommand()) {
            return;
        }

        const command = commandRegistry.get(interaction.commandName);
        if (!command) {
            return;
        }

        try {
            await command.execute(interaction);
        } catch (error) {
            const fallback = {
                content: "Something went wrong while executing this command.",
                ephemeral: true,
            };

            if (interaction.deferred || interaction.replied) {
                await interaction.editReply(fallback);
            } else {
                await interaction.reply(fallback);
            }

            console.error("Slash command execution failed", {
                command: interaction.commandName,
                error,
            });
        }
    },
};

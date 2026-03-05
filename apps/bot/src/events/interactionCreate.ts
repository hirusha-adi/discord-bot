import { Events, Interaction, MessageFlags } from "discord.js";
import { handleSlashCommand } from "../core/commands.js";

export const interactionCreateEvent = {
    name: Events.InteractionCreate,
    async execute(interaction: Interaction): Promise<void> {
        if (!interaction.isChatInputCommand()) {
            return;
        }

        try {
            await handleSlashCommand(interaction);
        } catch (error) {
            const payload = {
                content: "Something went wrong while executing this command.",
                flags: MessageFlags.Ephemeral,
            };

            if (interaction.deferred || interaction.replied) {
                await interaction.editReply(payload);
            } else {
                await interaction.reply(payload);
            }

            console.error("Slash command error", error);
        }
    },
};

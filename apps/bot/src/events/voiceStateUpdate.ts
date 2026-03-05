import { Events, VoiceState } from "discord.js";
import { prisma } from "../core/prisma.js";

export const voiceStateUpdateEvent = {
    name: Events.VoiceStateUpdate,
    async execute(oldState: VoiceState, newState: VoiceState): Promise<void> {
        if (!newState.guild.id) {
            return;
        }

        const actorId = newState.member?.id ?? oldState.member?.id;
        if (!actorId) {
            return;
        }

        await prisma.auditLog.create({
            data: {
                guildId: newState.guild.id,
                actorType: "DISCORD_USER",
                actorId,
                action: "VOICE_STATE_UPDATE",
                targetType: "VoiceState",
                targetId: actorId,
                metadataJson: JSON.stringify({
                    oldChannelId: oldState.channelId,
                    newChannelId: newState.channelId,
                }),
            },
        });
    },
};

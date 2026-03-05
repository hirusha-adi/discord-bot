import { interactionCreateEvent } from "./interactionCreate.js";
import { messageCreateEvent } from "./messageCreate.js";
import { guildMemberAddEvent } from "./guildMemberAdd.js";
import { guildMemberRemoveEvent } from "./guildMemberRemove.js";
import { guildUpdateEvent } from "./guildUpdate.js";
import { messageDeleteEvent } from "./messageDelete.js";
import { messageUpdateEvent } from "./messageUpdate.js";
import { reactionAddEvent } from "./reactionAdd.js";
import { reactionRemoveEvent } from "./reactionRemove.js";
import { voiceStateUpdateEvent } from "./voiceStateUpdate.js";

export const botEvents = [
    interactionCreateEvent,
    messageCreateEvent,
    guildMemberAddEvent,
    guildMemberRemoveEvent,
    guildUpdateEvent,
    messageDeleteEvent,
    messageUpdateEvent,
    reactionAddEvent,
    reactionRemoveEvent,
    voiceStateUpdateEvent,
] as const;

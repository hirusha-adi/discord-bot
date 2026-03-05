PRAGMA foreign_keys=OFF;

CREATE TABLE "Guilds" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "ownerDiscordId" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL
);

CREATE TABLE "GuildSettings" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "prefix" TEXT NOT NULL DEFAULT '!',
  "locale" TEXT NOT NULL DEFAULT 'en-US',
  "timezone" TEXT NOT NULL DEFAULT 'UTC',
  "logChannelId" TEXT,
  "modLogChannelId" TEXT,
  "welcomeChannelId" TEXT,
  "goodbyeChannelId" TEXT,
  "dashboardTheme" TEXT,
  "antiSpamEnabled" BOOLEAN NOT NULL DEFAULT false,
  "antiInviteEnabled" BOOLEAN NOT NULL DEFAULT false,
  "antiCapsEnabled" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "GuildSettings_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "GuildSettings_guildId_key" ON "GuildSettings"("guildId");

CREATE TABLE "GuildModules" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "moduleKey" TEXT NOT NULL,
  "enabled" BOOLEAN NOT NULL DEFAULT true,
  "configJson" TEXT,
  "configVersion" INTEGER NOT NULL DEFAULT 1,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "GuildModules_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "GuildModules_guildId_moduleKey_key" ON "GuildModules"("guildId", "moduleKey");
CREATE INDEX "GuildModules_guildId_idx" ON "GuildModules"("guildId");

CREATE TABLE "Users" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "username" TEXT,
  "discriminator" TEXT,
  "avatarUrl" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  "lastSeenAt" DATETIME
);

CREATE TABLE "DashboardAdmins" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "discordUserId" TEXT NOT NULL,
  "guildId" TEXT NOT NULL,
  "username" TEXT NOT NULL,
  "passwordHash" TEXT NOT NULL,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "lastLogin" DATETIME,
  "isActive" BOOLEAN NOT NULL DEFAULT true,
  CONSTRAINT "DashboardAdmins_discordUserId_fkey" FOREIGN KEY ("discordUserId") REFERENCES "Users" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "DashboardAdmins_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "DashboardAdmins_discordUserId_guildId_key" ON "DashboardAdmins"("discordUserId", "guildId");
CREATE INDEX "DashboardAdmins_guildId_username_idx" ON "DashboardAdmins"("guildId", "username");
CREATE INDEX "DashboardAdmins_discordUserId_idx" ON "DashboardAdmins"("discordUserId");

CREATE TABLE "Roles" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "discordRoleId" TEXT,
  "name" TEXT NOT NULL,
  "description" TEXT,
  "isSystem" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "Roles_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Roles_guildId_idx" ON "Roles"("guildId");

CREATE TABLE "Permissions" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "subjectType" TEXT NOT NULL,
  "subjectId" TEXT NOT NULL,
  "moduleKey" TEXT NOT NULL,
  "commandKey" TEXT,
  "action" TEXT NOT NULL,
  "effect" TEXT NOT NULL,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "Permissions_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Permissions_guildId_moduleKey_idx" ON "Permissions"("guildId", "moduleKey");
CREATE INDEX "Permissions_guildId_subjectType_subjectId_idx" ON "Permissions"("guildId", "subjectType", "subjectId");

CREATE TABLE "LevelingData" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "xp" INTEGER NOT NULL DEFAULT 0,
  "level" INTEGER NOT NULL DEFAULT 0,
  "messageCount" INTEGER NOT NULL DEFAULT 0,
  "lastMessageAt" DATETIME,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "LevelingData_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "LevelingData_userId_fkey" FOREIGN KEY ("userId") REFERENCES "Users" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "LevelingData_guildId_userId_key" ON "LevelingData"("guildId", "userId");
CREATE INDEX "LevelingData_guildId_xp_idx" ON "LevelingData"("guildId", "xp");

CREATE TABLE "ModerationLogs" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "caseNumber" INTEGER NOT NULL,
  "targetUserId" TEXT NOT NULL,
  "moderatorUserId" TEXT NOT NULL,
  "actionType" TEXT NOT NULL,
  "reason" TEXT,
  "durationSeconds" INTEGER,
  "active" BOOLEAN NOT NULL DEFAULT true,
  "appealNotes" TEXT,
  "modNotes" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  "expiresAt" DATETIME,
  CONSTRAINT "ModerationLogs_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "ModerationLogs_targetUserId_fkey" FOREIGN KEY ("targetUserId") REFERENCES "Users" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT "ModerationLogs_moderatorUserId_fkey" FOREIGN KEY ("moderatorUserId") REFERENCES "Users" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "ModerationLogs_guildId_caseNumber_key" ON "ModerationLogs"("guildId", "caseNumber");
CREATE INDEX "ModerationLogs_guildId_targetUserId_idx" ON "ModerationLogs"("guildId", "targetUserId");
CREATE INDEX "ModerationLogs_guildId_moderatorUserId_idx" ON "ModerationLogs"("guildId", "moderatorUserId");

CREATE TABLE "Automations" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "enabled" BOOLEAN NOT NULL DEFAULT true,
  "triggerType" TEXT NOT NULL,
  "conditionJson" TEXT NOT NULL,
  "actionJson" TEXT NOT NULL,
  "createdBy" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "Automations_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Automations_guildId_enabled_idx" ON "Automations"("guildId", "enabled");

CREATE TABLE "CustomCommands" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "responseType" TEXT NOT NULL,
  "responseText" TEXT,
  "responseEmbedJson" TEXT,
  "conditionsJson" TEXT,
  "cooldownSeconds" INTEGER NOT NULL DEFAULT 0,
  "requiredPermission" TEXT,
  "enabled" BOOLEAN NOT NULL DEFAULT true,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "CustomCommands_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "CustomCommands_guildId_name_key" ON "CustomCommands"("guildId", "name");
CREATE INDEX "CustomCommands_guildId_enabled_idx" ON "CustomCommands"("guildId", "enabled");

CREATE TABLE "ReactionRoles" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "channelId" TEXT NOT NULL,
  "messageId" TEXT NOT NULL,
  "emoji" TEXT NOT NULL,
  "roleId" TEXT NOT NULL,
  "removeOnUnreact" BOOLEAN NOT NULL DEFAULT true,
  "maxRolesPerUser" INTEGER,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "ReactionRoles_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "ReactionRoles_guildId_messageId_emoji_key" ON "ReactionRoles"("guildId", "messageId", "emoji");
CREATE INDEX "ReactionRoles_guildId_messageId_idx" ON "ReactionRoles"("guildId", "messageId");

CREATE TABLE "ScheduledTasks" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "taskType" TEXT NOT NULL,
  "payloadJson" TEXT NOT NULL,
  "executeAt" DATETIME NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "attempts" INTEGER NOT NULL DEFAULT 0,
  "maxAttempts" INTEGER NOT NULL DEFAULT 5,
  "lastError" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "ScheduledTasks_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "ScheduledTasks_guildId_status_executeAt_idx" ON "ScheduledTasks"("guildId", "status", "executeAt");

CREATE TABLE "WelcomeMessages" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "channelId" TEXT,
  "dmEnabled" BOOLEAN NOT NULL DEFAULT false,
  "enabled" BOOLEAN NOT NULL DEFAULT true,
  "messageTemplate" TEXT NOT NULL,
  "goodbyeTemplate" TEXT,
  "embedJson" TEXT,
  "imageEnabled" BOOLEAN NOT NULL DEFAULT false,
  "imageBackground" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "WelcomeMessages_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "WelcomeMessages_guildId_enabled_idx" ON "WelcomeMessages"("guildId", "enabled");

CREATE TABLE "TempBans" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "moderatorUserId" TEXT NOT NULL,
  "reason" TEXT,
  "startsAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "endsAt" DATETIME NOT NULL,
  "unbannedAt" DATETIME,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "TempBans_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "TempBans_guildId_userId_endsAt_idx" ON "TempBans"("guildId", "userId", "endsAt");

CREATE TABLE "Giveaways" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "channelId" TEXT NOT NULL,
  "messageId" TEXT,
  "title" TEXT NOT NULL,
  "description" TEXT,
  "winnerCount" INTEGER NOT NULL DEFAULT 1,
  "requiredRoleId" TEXT,
  "requiredLevel" INTEGER,
  "startsAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "endsAt" DATETIME NOT NULL,
  "endedAt" DATETIME,
  "createdBy" TEXT NOT NULL,
  "entryCount" INTEGER NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "Giveaways_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Giveaways_guildId_status_endsAt_idx" ON "Giveaways"("guildId", "status", "endsAt");

CREATE TABLE "Tickets" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "createdByUserId" TEXT NOT NULL,
  "assignedToUserId" TEXT,
  "channelId" TEXT NOT NULL,
  "categoryId" TEXT,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "subject" TEXT,
  "transcriptUrl" TEXT,
  "closedAt" DATETIME,
  "reopenedAt" DATETIME,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "Tickets_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "Tickets_createdByUserId_fkey" FOREIGN KEY ("createdByUserId") REFERENCES "Users" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX "Tickets_guildId_status_idx" ON "Tickets"("guildId", "status");
CREATE INDEX "Tickets_guildId_createdByUserId_idx" ON "Tickets"("guildId", "createdByUserId");

CREATE TABLE "EconomyBalances" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "balance" BIGINT NOT NULL DEFAULT 0,
  "bankBalance" BIGINT NOT NULL DEFAULT 0,
  "updatedAt" DATETIME NOT NULL,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EconomyBalances_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "EconomyBalances_userId_fkey" FOREIGN KEY ("userId") REFERENCES "Users" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX "EconomyBalances_guildId_userId_key" ON "EconomyBalances"("guildId", "userId");
CREATE INDEX "EconomyBalances_guildId_balance_idx" ON "EconomyBalances"("guildId", "balance");

CREATE TABLE "EconomyTransactions" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT NOT NULL,
  "actorUserId" TEXT NOT NULL,
  "targetUserId" TEXT,
  "txType" TEXT NOT NULL,
  "amount" BIGINT NOT NULL,
  "balanceAfter" BIGINT NOT NULL,
  "metadataJson" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "EconomyTransactions_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "EconomyTransactions_actorUserId_fkey" FOREIGN KEY ("actorUserId") REFERENCES "Users" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX "EconomyTransactions_guildId_actorUserId_createdAt_idx" ON "EconomyTransactions"("guildId", "actorUserId", "createdAt");

CREATE TABLE "AuditLogs" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "guildId" TEXT,
  "actorType" TEXT NOT NULL,
  "actorId" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "targetType" TEXT,
  "targetId" TEXT,
  "metadataJson" TEXT,
  "ipAddress" TEXT,
  "userAgent" TEXT,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "AuditLogs_guildId_fkey" FOREIGN KEY ("guildId") REFERENCES "Guilds" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX "AuditLogs_guildId_action_createdAt_idx" ON "AuditLogs"("guildId", "action", "createdAt");
CREATE INDEX "AuditLogs_actorId_createdAt_idx" ON "AuditLogs"("actorId", "createdAt");

CREATE TABLE "AdminSessions" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "dashboardAdminId" TEXT NOT NULL,
  "tokenHash" TEXT NOT NULL,
  "ipAddress" TEXT,
  "userAgent" TEXT,
  "expiresAt" DATETIME NOT NULL,
  "revokedAt" DATETIME,
  "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "AdminSessions_dashboardAdminId_fkey" FOREIGN KEY ("dashboardAdminId") REFERENCES "DashboardAdmins" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "AdminSessions_dashboardAdminId_expiresAt_idx" ON "AdminSessions"("dashboardAdminId", "expiresAt");
CREATE INDEX "AdminSessions_tokenHash_idx" ON "AdminSessions"("tokenHash");

PRAGMA foreign_keys=ON;

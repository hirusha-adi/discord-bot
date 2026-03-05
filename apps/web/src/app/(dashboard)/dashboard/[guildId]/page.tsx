"use client";

import { use, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { StatCard } from "@/components/dashboard/StatCard";
import { ModuleToggleCard } from "@/components/modules/ModuleToggleCard";

interface FeatureCatalogItem {
    moduleKey: string;
    title: string;
    description: string;
    defaultEnabled: boolean;
}

const FEATURE_CATALOG: FeatureCatalogItem[] = [
    {
        moduleKey: "moderation",
        title: "Moderation",
        description: "Ban, kick, mute, timeout, warn, and case tracking.",
        defaultEnabled: true,
    },
    {
        moduleKey: "leveling",
        title: "Leveling",
        description: "XP rules, cooldowns, and level reward controls.",
        defaultEnabled: true,
    },
    {
        moduleKey: "reaction-roles",
        title: "Reaction Roles",
        description: "Assign and remove roles using reactions, buttons, and menus.",
        defaultEnabled: true,
    },
    {
        moduleKey: "logging",
        title: "Logging",
        description: "Track moderation, message, role, and member events.",
        defaultEnabled: true,
    },
    {
        moduleKey: "automation",
        title: "Automation",
        description: "Run condition-action rules for routine moderation and ops.",
        defaultEnabled: true,
    },
    {
        moduleKey: "economy",
        title: "Economy",
        description: "Balances, rewards, and transaction-based server economy.",
        defaultEnabled: true,
    },
    {
        moduleKey: "tickets",
        title: "Tickets",
        description: "Create and manage support tickets with transcripts.",
        defaultEnabled: true,
    },
    {
        moduleKey: "giveaways",
        title: "Giveaways",
        description: "Create timed giveaways and pick winners with eligibility rules.",
        defaultEnabled: true,
    },
    {
        moduleKey: "welcome-goodbye",
        title: "Welcome and Goodbye",
        description: "Customize onboarding and departure messaging flows.",
        defaultEnabled: false,
    },
    {
        moduleKey: "custom-commands",
        title: "Custom Commands",
        description: "Create guild-specific text and embed command responses.",
        defaultEnabled: false,
    },
    {
        moduleKey: "analytics",
        title: "Analytics",
        description: "Track server trends, command usage, and moderation activity.",
        defaultEnabled: false,
    },
];

interface GuildPageData {
    guild: { id: string; name: string };
    settings: {
        prefix?: string;
        locale?: string;
        timezone?: string;
        logChannelId?: string | null;
        modLogChannelId?: string | null;
        welcomeChannelId?: string | null;
        goodbyeChannelId?: string | null;
        antiSpamEnabled?: boolean;
        antiInviteEnabled?: boolean;
        antiCapsEnabled?: boolean;
    } | null;
    modules: Array<{ moduleKey: string; enabled: boolean }>;
}

interface AnalyticsSummary {
    membersTracked: number;
    commandUsage: number;
    moderationActions: number;
    ticketsOpen: number;
}

interface SettingsForm {
    prefix: string;
    locale: string;
    timezone: string;
    logChannelId: string;
    modLogChannelId: string;
    welcomeChannelId: string;
    goodbyeChannelId: string;
    antiSpamEnabled: boolean;
    antiInviteEnabled: boolean;
    antiCapsEnabled: boolean;
}

function normalizeSettings(settings: GuildPageData["settings"]): SettingsForm {
    return {
        prefix: settings?.prefix ?? "!",
        locale: settings?.locale ?? "en-US",
        timezone: settings?.timezone ?? "UTC",
        logChannelId: settings?.logChannelId ?? "",
        modLogChannelId: settings?.modLogChannelId ?? "",
        welcomeChannelId: settings?.welcomeChannelId ?? "",
        goodbyeChannelId: settings?.goodbyeChannelId ?? "",
        antiSpamEnabled: settings?.antiSpamEnabled ?? false,
        antiInviteEnabled: settings?.antiInviteEnabled ?? false,
        antiCapsEnabled: settings?.antiCapsEnabled ?? false,
    };
}

export default function GuildSettingsPage({ params }: { params: Promise<{ guildId: string }> }) {
    const { guildId } = use(params);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);
    const [guildData, setGuildData] = useState<GuildPageData | null>(null);
    const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
    const [moduleSavingKey, setModuleSavingKey] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const [form, setForm] = useState<SettingsForm>({
        prefix: "!",
        locale: "en-US",
        timezone: "UTC",
        logChannelId: "",
        modLogChannelId: "",
        welcomeChannelId: "",
        goodbyeChannelId: "",
        antiSpamEnabled: false,
        antiInviteEnabled: false,
        antiCapsEnabled: false,
    });

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const [guildPayload, analyticsPayload] = await Promise.all([
                    apiFetch<GuildPageData>(`/guilds/${guildId}`),
                    apiFetch<AnalyticsSummary>(`/guilds/${guildId}/analytics/summary`),
                ]);

                if (cancelled) {
                    return;
                }

                setGuildData(guildPayload);
                setAnalytics(analyticsPayload);
                setForm(normalizeSettings(guildPayload.settings));
            } catch (err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : "Failed to load guild dashboard.");
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [guildId]);

    const moduleStateMap = useMemo(() => {
        const map = new Map<string, boolean>();
        for (const moduleRecord of guildData?.modules ?? []) {
            map.set(moduleRecord.moduleKey, moduleRecord.enabled);
        }
        return map;
    }, [guildData]);

    const featureList = useMemo(() => {
        return FEATURE_CATALOG.map((feature) => ({
            ...feature,
            enabled: moduleStateMap.get(feature.moduleKey) ?? feature.defaultEnabled,
        }));
    }, [moduleStateMap]);

    async function saveSettings(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setMessage(null);

        try {
            await apiFetch(`/guilds/${guildId}/settings`, {
                method: "PUT",
                body: JSON.stringify({
                    ...form,
                    logChannelId: form.logChannelId || null,
                    modLogChannelId: form.modLogChannelId || null,
                    welcomeChannelId: form.welcomeChannelId || null,
                    goodbyeChannelId: form.goodbyeChannelId || null,
                }),
            });
            setMessage("General settings saved.");
        } catch (err) {
            setMessage(err instanceof Error ? err.message : "Could not save settings.");
        } finally {
            setSaving(false);
        }
    }

    async function toggleModule(moduleKey: string, enabled: boolean) {
        setModuleSavingKey(moduleKey);
        setMessage(null);
        try {
            const response = await apiFetch<{ module: { moduleKey: string; enabled: boolean } }>(
                `/guilds/${guildId}/modules/${moduleKey}`,
                {
                    method: "PUT",
                    body: JSON.stringify({ enabled }),
                },
            );

            setGuildData((previous) => {
                if (!previous) return previous;

                const exists = previous.modules.some((mod) => mod.moduleKey === moduleKey);
                const nextModules = exists
                    ? previous.modules.map((mod) =>
                        mod.moduleKey === moduleKey ? { ...mod, enabled: response.module.enabled } : mod,
                    )
                    : [...previous.modules, { moduleKey, enabled: response.module.enabled }];

                return {
                    ...previous,
                    modules: nextModules,
                };
            });

            setMessage(`${moduleKey} ${enabled ? "enabled" : "disabled"}.`);
        } catch (err) {
            setMessage(err instanceof Error ? err.message : "Failed to update module.");
        } finally {
            setModuleSavingKey(null);
        }
    }

    if (loading) {
        return (
            <main>
                <p className="muted-text">Loading guild dashboard...</p>
            </main>
        );
    }

    if (error || !guildData) {
        return (
            <main>
                <p className="error-text">{error ?? "Guild not found."}</p>
            </main>
        );
    }

    return (
        <main className="grid">
            <section className="card page-head">
                <h1>{guildData.guild.name}</h1>
                <p className="muted-text mono">Guild ID: {guildData.guild.id}</p>
            </section>

            <section className="grid stat-grid">
                <StatCard label="Members Tracked" value={analytics?.membersTracked ?? 0} />
                <StatCard label="Command Usage" value={analytics?.commandUsage ?? 0} />
                <StatCard label="Moderation Actions" value={analytics?.moderationActions ?? 0} />
                <StatCard label="Open Tickets" value={analytics?.ticketsOpen ?? 0} />
            </section>

            <section className="card">
                <h2>General Settings</h2>
                <form className="grid settings-grid" onSubmit={saveSettings}>
                    <label>
                        Prefix
                        <input value={form.prefix} maxLength={5} onChange={(e) => setForm((prev) => ({ ...prev, prefix: e.target.value }))} />
                    </label>
                    <label>
                        Locale
                        <input value={form.locale} onChange={(e) => setForm((prev) => ({ ...prev, locale: e.target.value }))} />
                    </label>
                    <label>
                        Timezone
                        <input value={form.timezone} onChange={(e) => setForm((prev) => ({ ...prev, timezone: e.target.value }))} />
                    </label>
                    <label>
                        Log Channel ID
                        <input value={form.logChannelId} onChange={(e) => setForm((prev) => ({ ...prev, logChannelId: e.target.value }))} />
                    </label>
                    <label>
                        Moderation Log Channel ID
                        <input value={form.modLogChannelId} onChange={(e) => setForm((prev) => ({ ...prev, modLogChannelId: e.target.value }))} />
                    </label>
                    <label>
                        Welcome Channel ID
                        <input value={form.welcomeChannelId} onChange={(e) => setForm((prev) => ({ ...prev, welcomeChannelId: e.target.value }))} />
                    </label>
                    <label>
                        Goodbye Channel ID
                        <input value={form.goodbyeChannelId} onChange={(e) => setForm((prev) => ({ ...prev, goodbyeChannelId: e.target.value }))} />
                    </label>

                    <label className="toggle-row">
                        <input type="checkbox" checked={form.antiSpamEnabled} onChange={(e) => setForm((prev) => ({ ...prev, antiSpamEnabled: e.target.checked }))} />
                        Anti Spam
                    </label>
                    <label className="toggle-row">
                        <input type="checkbox" checked={form.antiInviteEnabled} onChange={(e) => setForm((prev) => ({ ...prev, antiInviteEnabled: e.target.checked }))} />
                        Invite Blocking
                    </label>
                    <label className="toggle-row">
                        <input type="checkbox" checked={form.antiCapsEnabled} onChange={(e) => setForm((prev) => ({ ...prev, antiCapsEnabled: e.target.checked }))} />
                        Caps Protection
                    </label>

                    <div>
                        <button className="btn btn-primary" type="submit" disabled={saving}>
                            {saving ? "Saving..." : "Save Settings"}
                        </button>
                    </div>
                </form>
            </section>

            <section className="card">
                <h2>Feature Selection</h2>
                <p className="muted-text">Enable or disable features for this guild. Changes are saved immediately per toggle.</p>
                <div className="grid module-grid">
                    {featureList.map((feature) => (
                        <ModuleToggleCard
                            key={feature.moduleKey}
                            moduleKey={feature.moduleKey}
                            title={feature.title}
                            description={feature.description}
                            enabled={feature.enabled}
                            pending={moduleSavingKey === feature.moduleKey}
                            onToggle={(nextValue) => toggleModule(feature.moduleKey, nextValue)}
                        />
                    ))}
                </div>
            </section>

            {message ? <p className="muted-text">{message}</p> : null}
        </main>
    );
}

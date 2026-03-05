"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { StatCard } from "@/components/dashboard/StatCard";
import { ModuleToggleCard } from "@/components/modules/ModuleToggleCard";

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

export default function GuildSettingsPage({ params }: { params: { guildId: string } }) {
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
                    apiFetch<GuildPageData>(`/guilds/${params.guildId}`),
                    apiFetch<AnalyticsSummary>(`/guilds/${params.guildId}/analytics/summary`),
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
    }, [params.guildId]);

    const moduleList = useMemo(() => guildData?.modules ?? [], [guildData]);

    async function saveSettings(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setMessage(null);

        try {
            await apiFetch(`/guilds/${params.guildId}/settings`, {
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
                `/guilds/${params.guildId}/modules/${moduleKey}`,
                {
                    method: "PUT",
                    body: JSON.stringify({ enabled }),
                },
            );

            setGuildData((previous) => {
                if (!previous) return previous;
                return {
                    ...previous,
                    modules: previous.modules.map((mod) =>
                        mod.moduleKey === moduleKey ? { ...mod, enabled: response.module.enabled } : mod,
                    ),
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
                <h2>Modules</h2>
                <div className="grid module-grid">
                    {moduleList.map((moduleConfig) => (
                        <ModuleToggleCard
                            key={moduleConfig.moduleKey}
                            moduleKey={moduleConfig.moduleKey}
                            enabled={moduleConfig.enabled}
                            pending={moduleSavingKey === moduleConfig.moduleKey}
                            onToggle={(nextValue) => toggleModule(moduleConfig.moduleKey, nextValue)}
                        />
                    ))}
                </div>
            </section>

            <section className="card">
                <h2>Feature Sections</h2>
                <div className="grid section-grid">
                    <article className="card section-card"><h3>Moderation</h3><p className="muted-text">Ban, kick, mute, timeout, warn, logs, and case tracking.</p></article>
                    <article className="card section-card"><h3>Auto Moderation</h3><p className="muted-text">Spam, bad words, links, invite blocking, caps detection.</p></article>
                    <article className="card section-card"><h3>Custom Commands</h3><p className="muted-text">Template responses with variables and permission checks.</p></article>
                    <article className="card section-card"><h3>Welcome & Goodbye</h3><p className="muted-text">Message templates, embed builder, and DM welcome options.</p></article>
                    <article className="card section-card"><h3>Leveling</h3><p className="muted-text">XP settings, anti-spam cooldowns, reward roles, and announcements.</p></article>
                    <article className="card section-card"><h3>Reaction Roles</h3><p className="muted-text">Reaction, button, and menu role assignment controls.</p></article>
                    <article className="card section-card"><h3>Automation</h3><p className="muted-text">Condition-action rules for joins, keywords, and scheduling.</p></article>
                    <article className="card section-card"><h3>Economy</h3><p className="muted-text">Daily rewards, balances, transfers, and leaderboard controls.</p></article>
                    <article className="card section-card"><h3>Giveaways</h3><p className="muted-text">Duration, winner count, eligibility, and reroll behavior.</p></article>
                    <article className="card section-card"><h3>Tickets</h3><p className="muted-text">Ticket channels, transcripts, staff roles, and categories.</p></article>
                    <article className="card section-card"><h3>Logging</h3><p className="muted-text">Per-event log channels for messages, roles, and moderation.</p></article>
                    <article className="card section-card"><h3>Analytics</h3><p className="muted-text">Server growth, usage stats, and moderation trend summaries.</p></article>
                </div>
            </section>

            {message ? <p className="muted-text">{message}</p> : null}
        </main>
    );
}

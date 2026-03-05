"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

interface GuildItem {
    guildId: string;
    name: string;
    ownerDiscordId?: string;
}

export default function DashboardPage() {
    const [guilds, setGuilds] = useState<GuildItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function loadGuilds() {
            try {
                const data = await apiFetch<{ guilds: GuildItem[] }>("/guilds");
                if (!cancelled) {
                    setGuilds(data.guilds);
                    setError(null);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : "Failed to load guilds");
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        loadGuilds();
        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <main>
            <section className="page-head">
                <h1>Servers You Manage</h1>
                <p className="muted-text">Select a guild to configure modules, automation, moderation, and analytics.</p>
            </section>

            {loading ? <p className="muted-text">Loading guilds...</p> : null}
            {error ? <p className="error-text">{error}</p> : null}

            <div className="grid guild-grid">
                {guilds.map((guild) => (
                    <article key={guild.guildId} className="card guild-card">
                        <h2>{guild.name}</h2>
                        <p className="muted-text mono">Guild ID: {guild.guildId}</p>
                        <Link href={`/dashboard/${guild.guildId}`} className="link-accent">
                            Open Dashboard
                        </Link>
                    </article>
                ))}
            </div>

            {!loading && !error && guilds.length === 0 ? (
                <section className="card" style={{ marginTop: "1rem" }}>
                    <p className="muted-text">No managed servers found for this session.</p>
                    <p className="muted-text">Run <code>/create-dashboard-admin</code> in your guild to provision dashboard access.</p>
                </section>
            ) : null}
        </main>
    );
}

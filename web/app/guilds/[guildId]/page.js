'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function GuildOverviewPage({ params }) {
  const { guildId } = params;
  const [overview, setOverview] = useState(null);
  const [status, setStatus] = useState('Loading overview...');

  useEffect(() => {
    const loadOverview = async () => {
      const response = await fetch(`${API_BASE}/guilds/${guildId}/overview`, {
        method: 'GET',
        credentials: 'include'
      });

      const data = await response.json();
      if (!response.ok) {
        setStatus(data.detail || 'Failed to load overview');
        return;
      }

      setOverview(data);
      setStatus('Overview loaded');
    };

    loadOverview();
  }, [guildId]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 py-10">
      <header className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-semibold">Guild Overview</h1>
        <p className="mt-2 text-sm text-slate-300">{status}</p>
      </header>

      {overview ? (
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">{overview.guild.name}</h2>
              <p className="text-sm text-slate-300">Guild ID: {overview.guild.id}</p>
            </div>
            <div className="flex gap-2">
              <Link href={`/guilds/${guildId}/audit-logs`} className="rounded-md bg-sky-700 px-3 py-2 text-sm font-medium hover:bg-sky-600">Audit Logs</Link>
              <Link href={`/guilds/${guildId}/modules`} className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium hover:bg-emerald-500">Open Modules</Link>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h3 className="font-medium">Stats</h3>
              <pre className="mt-2 overflow-x-auto text-xs text-slate-300">{JSON.stringify(overview.stats, null, 2)}</pre>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h3 className="font-medium">Modules (Read-only)</h3>
              <ul className="mt-2 space-y-1 text-sm text-slate-300">
                {overview.modules.map((module) => (
                  <li key={module.key}>
                    {module.key}: {module.enabled ? 'enabled' : 'disabled'}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      ) : null}

      <Link href="/guilds" className="text-sm text-sky-300 hover:text-sky-200">Back to Guilds</Link>
    </main>
  );
}

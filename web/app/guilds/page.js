'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function GuildsPage() {
  const [guilds, setGuilds] = useState([]);
  const [status, setStatus] = useState('Loading guilds...');

  useEffect(() => {
    const loadGuilds = async () => {
      const response = await fetch(`${API_BASE}/guilds`, {
        method: 'GET',
        credentials: 'include'
      });

      const data = await response.json();
      if (!response.ok) {
        setStatus(data.detail || 'Failed to load guilds');
        return;
      }

      setGuilds(data);
      setStatus(data.length === 0 ? 'No manageable guilds where bot is present.' : 'Guilds loaded');
    };

    loadGuilds();
  }, []);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col gap-6 px-6 py-10">
      <header className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-semibold">Guild Selection</h1>
        <p className="mt-2 text-sm text-slate-300">{status}</p>
      </header>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <ul className="space-y-3">
          {guilds.map((guild) => (
            <li key={guild.id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 px-4 py-3">
              <span className="font-medium">{guild.name}</span>
              <div className="flex gap-2">
                <Link href={`/guilds/${guild.id}`} className="rounded-md bg-slate-700 px-3 py-1.5 text-sm hover:bg-slate-600">Overview</Link>
                <Link href={`/guilds/${guild.id}/modules`} className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm hover:bg-emerald-500">Modules</Link>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <Link href="/" className="text-sm text-sky-300 hover:text-sky-200">Back to Login</Link>
    </main>
  );
}

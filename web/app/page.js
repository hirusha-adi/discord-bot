'use client';

import Link from 'next/link';
import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function HomePage() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('Not authenticated');

  const callAuth = async (path) => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password })
    });

    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail || 'Request failed');
      return;
    }

    setMessage(`Authenticated as user #${data.user.id}`);
  };

  const checkSession = async () => {
    const response = await fetch(`${API_BASE}/auth/me`, {
      method: 'GET',
      credentials: 'include'
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail || 'No active session');
      return;
    }
    setMessage(`Session active for user #${data.user.id}`);
  };

  const loginWithDiscord = () => {
    window.location.href = `${API_BASE}/auth/discord/login`;
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col gap-6 px-6 py-10">
      <header className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-semibold">Discord Bot Dashboard Login</h1>
        <p className="mt-2 text-sm text-slate-300">Stage 4 module management baseline.</p>
      </header>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div className="grid gap-4">
          <div>
            <label htmlFor="identifier" className="mb-1 block text-sm font-medium text-slate-300">Username or Email</label>
            <input
              id="identifier"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none ring-sky-500 focus:ring"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-300">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none ring-sky-500 focus:ring"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <button onClick={() => callAuth('/auth/local/register')} className="rounded-md bg-sky-600 px-3 py-2 text-sm font-medium hover:bg-sky-500">Register + Login</button>
            <button onClick={() => callAuth('/auth/local/login')} className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium hover:bg-slate-600">Login</button>
            <button onClick={checkSession} className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium hover:bg-slate-600">Check Session</button>
            <button onClick={loginWithDiscord} className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium hover:bg-indigo-500">Login with Discord</button>
            <Link href="/guilds" className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium hover:bg-emerald-500">Go to Guilds</Link>
          </div>

          <p className="text-sm text-slate-200"><span className="font-semibold">Status:</span> {message}</p>
        </div>
      </section>
    </main>
  );
}

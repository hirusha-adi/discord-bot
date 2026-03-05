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
    <main style={{ fontFamily: 'sans-serif', maxWidth: 620, margin: '40px auto', padding: '0 16px' }}>
      <h1>Discord Bot Dashboard Login</h1>
      <p>Stage 3 authentication + guild discovery baseline.</p>

      <label htmlFor="identifier">Username or Email</label>
      <input
        id="identifier"
        value={identifier}
        onChange={(e) => setIdentifier(e.target.value)}
        style={{ width: '100%', marginBottom: 12, padding: 8 }}
      />

      <label htmlFor="password">Password</label>
      <input
        id="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{ width: '100%', marginBottom: 16, padding: 8 }}
      />

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={() => callAuth('/auth/local/register')}>Register + Login</button>
        <button onClick={() => callAuth('/auth/local/login')}>Login</button>
        <button onClick={checkSession}>Check Session</button>
        <button onClick={loginWithDiscord}>Login with Discord</button>
        <Link href="/guilds" style={{ alignSelf: 'center' }}>Go to Guilds</Link>
      </div>

      <p style={{ marginTop: 16 }}>
        <strong>Status:</strong> {message}
      </p>
    </main>
  );
}

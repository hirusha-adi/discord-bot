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
    <main style={{ fontFamily: 'sans-serif', maxWidth: 720, margin: '40px auto', padding: '0 16px' }}>
      <h1>Guild Selection</h1>
      <p>{status}</p>

      <ul style={{ paddingLeft: 20 }}>
        {guilds.map((guild) => (
          <li key={guild.id} style={{ marginBottom: 10 }}>
            <Link href={`/guilds/${guild.id}`}>{guild.name}</Link>
          </li>
        ))}
      </ul>
    </main>
  );
}

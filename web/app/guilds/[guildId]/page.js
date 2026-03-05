'use client';

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
    <main style={{ fontFamily: 'sans-serif', maxWidth: 760, margin: '40px auto', padding: '0 16px' }}>
      <h1>Guild Overview</h1>
      <p>{status}</p>

      {overview ? (
        <>
          <h2>{overview.guild.name}</h2>
          <p>Guild ID: {overview.guild.id}</p>

          <h3>Stats</h3>
          <pre style={{ background: '#f2f2f2', padding: 12 }}>{JSON.stringify(overview.stats, null, 2)}</pre>

          <h3>Modules (Read-only)</h3>
          <ul style={{ paddingLeft: 20 }}>
            {overview.modules.map((module) => (
              <li key={module.key}>
                {module.key}: {module.enabled ? 'enabled' : 'disabled'}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </main>
  );
}

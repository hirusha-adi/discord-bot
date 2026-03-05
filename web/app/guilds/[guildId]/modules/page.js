'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const MODULE_KEYS = ['welcome', 'leave', 'verification', 'audit', 'announcement'];

const initialState = {
  welcome: { enabled: false, markdown_text: '', image_urls_text: '' },
  leave: { enabled: false, markdown_text: '', image_urls_text: '' },
  verification: { enabled: false, role_ids_text: '' },
  audit: { enabled: false, destination_type: 'dashboard', log_channel_id: '' },
  announcement: { enabled: false, default_channel_id: '' }
};

function parseList(text) {
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function GuildModulesPage({ params }) {
  const { guildId } = params;
  const [state, setState] = useState(initialState);
  const [status, setStatus] = useState('Loading module configs...');

  const moduleLabels = useMemo(
    () => ({
      welcome: 'Welcome DM',
      leave: 'Leave DM',
      verification: 'Verification',
      audit: 'Audit Logging',
      announcement: 'Announcements'
    }),
    []
  );

  const loadModule = async (module) => {
    const response = await fetch(`${API_BASE}/guilds/${guildId}/modules/${module}`, {
      method: 'GET',
      credentials: 'include'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `Failed to load ${module}`);
    }
    return data;
  };

  useEffect(() => {
    const loadAll = async () => {
      try {
        const loaded = {};
        for (const module of MODULE_KEYS) {
          const config = await loadModule(module);
          if (module === 'welcome' || module === 'leave') {
            loaded[module] = {
              enabled: config.enabled,
              markdown_text: config.config.markdown_text || '',
              image_urls_text: (config.config.image_urls || []).join(', ')
            };
          } else if (module === 'verification') {
            loaded[module] = {
              enabled: config.enabled,
              role_ids_text: (config.config.role_ids || []).join(', ')
            };
          } else if (module === 'audit') {
            loaded[module] = {
              enabled: config.enabled,
              destination_type: config.config.destination_type || 'dashboard',
              log_channel_id: config.config.log_channel_id || ''
            };
          } else {
            loaded[module] = {
              enabled: config.enabled,
              default_channel_id: config.config.default_channel_id || ''
            };
          }
        }

        setState((prev) => ({ ...prev, ...loaded }));
        setStatus('Module configs loaded');
      } catch (error) {
        setStatus(error.message);
      }
    };

    loadAll();
  }, [guildId]);

  const onToggle = async (module, enabled) => {
    const response = await fetch(`${API_BASE}/guilds/${guildId}/modules/${module}/toggle`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });

    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || `Failed to toggle ${module}`);
      return;
    }

    setState((prev) => ({ ...prev, [module]: { ...prev[module], enabled: data.enabled } }));
    setStatus(`${moduleLabels[module]} toggle saved`);
  };

  const onSave = async (module) => {
    let payload = {};
    if (module === 'welcome' || module === 'leave') {
      payload = {
        enabled: state[module].enabled,
        markdown_text: state[module].markdown_text,
        image_urls: parseList(state[module].image_urls_text)
      };
    } else if (module === 'verification') {
      payload = {
        enabled: state[module].enabled,
        role_ids: parseList(state[module].role_ids_text)
      };
    } else if (module === 'audit') {
      payload = {
        enabled: state[module].enabled,
        destination_type: state[module].destination_type,
        log_channel_id: state[module].log_channel_id || null
      };
    } else {
      payload = {
        enabled: state[module].enabled,
        default_channel_id: state[module].default_channel_id || null
      };
    }

    const response = await fetch(`${API_BASE}/guilds/${guildId}/modules/${module}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || `Failed to save ${module}`);
      return;
    }

    setStatus(`${moduleLabels[module]} config saved`);
    setState((prev) => ({ ...prev, [module]: { ...prev[module], enabled: data.enabled } }));
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-6 py-10">
      <header className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-semibold">Guild Modules</h1>
        <p className="mt-2 text-sm text-slate-300">Guild ID: {guildId}</p>
        <p className="mt-1 text-sm text-slate-300">{status}</p>
      </header>

      <section className="grid gap-5">
        {MODULE_KEYS.map((module) => (
          <article key={module} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{moduleLabels[module]}</h2>
              <label className="inline-flex items-center gap-2 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={state[module].enabled}
                  onChange={(e) => onToggle(module, e.target.checked)}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-950 text-emerald-500"
                />
                Enabled
              </label>
            </div>

            {(module === 'welcome' || module === 'leave') && (
              <div className="grid gap-3">
                <label className="text-sm text-slate-300">Markdown Text</label>
                <textarea
                  value={state[module].markdown_text}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, [module]: { ...prev[module], markdown_text: e.target.value } }))
                  }
                  className="min-h-28 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
                />
                <label className="text-sm text-slate-300">Image URLs (comma-separated)</label>
                <input
                  value={state[module].image_urls_text}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, [module]: { ...prev[module], image_urls_text: e.target.value } }))
                  }
                  className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
                />
              </div>
            )}

            {module === 'verification' && (
              <div className="grid gap-3">
                <label className="text-sm text-slate-300">Role IDs (comma-separated)</label>
                <input
                  value={state.verification.role_ids_text}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, verification: { ...prev.verification, role_ids_text: e.target.value } }))
                  }
                  className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
                />
              </div>
            )}

            {module === 'audit' && (
              <div className="grid gap-3">
                <label className="text-sm text-slate-300">Destination Type</label>
                <select
                  value={state.audit.destination_type}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, audit: { ...prev.audit, destination_type: e.target.value } }))
                  }
                  className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
                >
                  <option value="dashboard">Dashboard</option>
                  <option value="channel">Channel</option>
                </select>

                <label className="text-sm text-slate-300">Log Channel ID</label>
                <input
                  value={state.audit.log_channel_id}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, audit: { ...prev.audit, log_channel_id: e.target.value } }))
                  }
                  className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
                />
              </div>
            )}

            {module === 'announcement' && (
              <div className="grid gap-3">
                <label className="text-sm text-slate-300">Default Channel ID</label>
                <input
                  value={state.announcement.default_channel_id}
                  onChange={(e) =>
                    setState((prev) => ({
                      ...prev,
                      announcement: { ...prev.announcement, default_channel_id: e.target.value }
                    }))
                  }
                  className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
                />
              </div>
            )}

            <div className="mt-4">
              <button
                onClick={() => onSave(module)}
                className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium hover:bg-emerald-500"
              >
                Save {moduleLabels[module]}
              </button>
            </div>
          </article>
        ))}
      </section>

      <div className="flex gap-4 text-sm">
        <Link href={`/guilds/${guildId}`} className="text-sky-300 hover:text-sky-200">Back to Overview</Link>
        <Link href="/guilds" className="text-sky-300 hover:text-sky-200">Back to Guilds</Link>
      </div>
    </main>
  );
}

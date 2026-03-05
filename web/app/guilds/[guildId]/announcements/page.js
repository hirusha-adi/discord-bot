'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

function parseCsv(text) {
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function GuildAnnouncementsPage({ params }) {
  const { guildId } = params;
  const [status, setStatus] = useState('Loading announcements...');
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({
    content: '',
    channel_id: '',
    use_default_channel: true,
    image_urls_text: '',
    mention_policy: 'none',
    role_ids_text: '',
    scheduled_at: ''
  });

  const loadScheduled = async () => {
    const response = await fetch(`${API_BASE}/guilds/${guildId}/announcements/scheduled?limit=50&offset=0`, {
      method: 'GET',
      credentials: 'include'
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || 'Failed to load scheduled announcements');
      return;
    }
    setItems(data.items || []);
    setStatus(`Loaded ${data.items.length} scheduled announcements`);
  };

  useEffect(() => {
    loadScheduled();
  }, [guildId]);

  const buildPayload = () => ({
    content: form.content,
    channel_id: form.use_default_channel ? null : form.channel_id.trim() || null,
    image_urls: parseCsv(form.image_urls_text),
    mention_policy: form.mention_policy,
    role_ids: form.mention_policy === 'roles' ? parseCsv(form.role_ids_text) : []
  });

  const sendNow = async () => {
    const response = await fetch(`${API_BASE}/guilds/${guildId}/announcements/send-now`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildPayload())
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || 'Send now failed');
      return;
    }
    setStatus(`Announcement sent to channel ${data.channel_id}`);
  };

  const schedule = async () => {
    if (!form.scheduled_at) {
      setStatus('Choose a schedule datetime first');
      return;
    }

    const response = await fetch(`${API_BASE}/guilds/${guildId}/announcements/scheduled`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...buildPayload(),
        scheduled_at: new Date(form.scheduled_at).toISOString()
      })
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || 'Schedule failed');
      return;
    }

    setStatus(`Scheduled announcement #${data.id}`);
    await loadScheduled();
  };

  const cancelScheduled = async (id) => {
    const response = await fetch(`${API_BASE}/guilds/${guildId}/announcements/scheduled/${id}/cancel`, {
      method: 'PATCH',
      credentials: 'include'
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || 'Cancel failed');
      return;
    }

    setStatus(`Cancelled announcement #${data.id}`);
    await loadScheduled();
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <header className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-semibold">Announcements</h1>
        <p className="mt-2 text-sm text-slate-300">Guild ID: {guildId}</p>
        <p className="mt-1 text-sm text-slate-300">{status}</p>
      </header>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h2 className="text-lg font-semibold">Compose Announcement</h2>
        <div className="mt-3 grid gap-3">
          <label className="text-sm text-slate-300">Content</label>
          <textarea
            value={form.content}
            onChange={(e) => setForm((prev) => ({ ...prev, content: e.target.value }))}
            className="min-h-32 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
          />

          <label className="inline-flex items-center gap-2 text-sm text-slate-200">
            <input
              type="checkbox"
              checked={form.use_default_channel}
              onChange={(e) => setForm((prev) => ({ ...prev, use_default_channel: e.target.checked }))}
              className="h-4 w-4 rounded border-slate-600 bg-slate-950 text-emerald-500"
            />
            Use default channel from module config
          </label>

          {!form.use_default_channel ? (
            <>
              <label className="text-sm text-slate-300">Channel ID</label>
              <input
                value={form.channel_id}
                onChange={(e) => setForm((prev) => ({ ...prev, channel_id: e.target.value }))}
                className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
              />
            </>
          ) : null}

          <label className="text-sm text-slate-300">Image URLs (comma-separated)</label>
          <input
            value={form.image_urls_text}
            onChange={(e) => setForm((prev) => ({ ...prev, image_urls_text: e.target.value }))}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
          />

          <label className="text-sm text-slate-300">Mentions</label>
          <select
            value={form.mention_policy}
            onChange={(e) => setForm((prev) => ({ ...prev, mention_policy: e.target.value }))}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
          >
            <option value="none">none</option>
            <option value="everyone">@everyone</option>
            <option value="roles">roles</option>
          </select>

          {form.mention_policy === 'roles' ? (
            <>
              <label className="text-sm text-slate-300">Role IDs (comma-separated)</label>
              <input
                value={form.role_ids_text}
                onChange={(e) => setForm((prev) => ({ ...prev, role_ids_text: e.target.value }))}
                className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
              />
            </>
          ) : null}

          <div className="mt-1 flex flex-wrap gap-2">
            <button onClick={sendNow} className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium hover:bg-emerald-500">
              Send now
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h2 className="text-lg font-semibold">Schedule</h2>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div className="grid gap-1">
            <label className="text-sm text-slate-300">Datetime (local)</label>
            <input
              type="datetime-local"
              value={form.scheduled_at}
              onChange={(e) => setForm((prev) => ({ ...prev, scheduled_at: e.target.value }))}
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
            />
          </div>
          <button onClick={schedule} className="rounded-md bg-sky-700 px-3 py-2 text-sm font-medium hover:bg-sky-600">
            Schedule
          </button>
          <button onClick={loadScheduled} className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium hover:bg-slate-600">
            Refresh statuses
          </button>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-800/70 text-slate-200">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Scheduled</th>
                <th className="px-3 py-2">Channel</th>
                <th className="px-3 py-2">Sent At</th>
                <th className="px-3 py-2">Error</th>
                <th className="px-3 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-slate-800">
                  <td className="px-3 py-2 text-slate-300">{item.id}</td>
                  <td className="px-3 py-2 text-slate-200">{item.status}</td>
                  <td className="px-3 py-2 text-slate-300">{new Date(item.scheduled_at).toLocaleString()}</td>
                  <td className="px-3 py-2 text-slate-300">{item.channel_id || 'default'}</td>
                  <td className="px-3 py-2 text-slate-300">{item.sent_at ? new Date(item.sent_at).toLocaleString() : ''}</td>
                  <td className="max-w-sm whitespace-pre-wrap break-words px-3 py-2 text-slate-300">{item.error_message || ''}</td>
                  <td className="px-3 py-2">
                    {item.status === 'pending' ? (
                      <button
                        onClick={() => cancelScheduled(item.id)}
                        className="rounded-md bg-rose-700 px-3 py-1.5 text-xs font-medium hover:bg-rose-600"
                      >
                        Cancel
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
              {items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-slate-400">
                    No scheduled announcements yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <div className="flex gap-4 text-sm">
        <Link href={`/guilds/${guildId}`} className="text-sky-300 hover:text-sky-200">
          Back to Overview
        </Link>
        <Link href={`/guilds/${guildId}/modules`} className="text-sky-300 hover:text-sky-200">
          Back to Modules
        </Link>
        <Link href="/guilds" className="text-sky-300 hover:text-sky-200">
          Back to Guilds
        </Link>
      </div>
    </main>
  );
}

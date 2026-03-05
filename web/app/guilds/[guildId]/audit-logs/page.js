'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const PAGE_SIZE = 25;

function toLocalInputValue(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function AuditLogsPage({ params }) {
  const { guildId } = params;
  const [status, setStatus] = useState('Loading audit logs...');
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [filters, setFilters] = useState({
    event_type: '',
    channel_id: '',
    author_id: '',
    occurred_from: '',
    occurred_to: ''
  });

  const canPrev = offset > 0;
  const canNext = useMemo(() => offset + PAGE_SIZE < total, [offset, total]);

  const buildQueryString = () => {
    const query = new URLSearchParams();
    if (filters.event_type) query.set('event_type', filters.event_type);
    if (filters.channel_id) query.set('channel_id', filters.channel_id.trim());
    if (filters.author_id) query.set('author_id', filters.author_id.trim());
    if (filters.occurred_from) query.set('occurred_from', new Date(filters.occurred_from).toISOString());
    if (filters.occurred_to) query.set('occurred_to', new Date(filters.occurred_to).toISOString());
    query.set('limit', String(PAGE_SIZE));
    query.set('offset', String(offset));
    return query.toString();
  };

  useEffect(() => {
    const loadLogs = async () => {
      setStatus('Loading audit logs...');
      const response = await fetch(`${API_BASE}/guilds/${guildId}/audit-logs?${buildQueryString()}`, {
        method: 'GET',
        credentials: 'include'
      });
      const data = await response.json();
      if (!response.ok) {
        setStatus(data.detail || 'Failed to load audit logs');
        setRows([]);
        setTotal(0);
        return;
      }

      setRows(data.items || []);
      setTotal(data.total || 0);
      setStatus(`Loaded ${data.items.length} / ${data.total} events`);
    };

    loadLogs();
  }, [guildId, offset, filters]);

  const onFilterChange = (key, value) => {
    setOffset(0);
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const setLast24h = () => {
    const now = new Date();
    const since = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    setOffset(0);
    setFilters((prev) => ({
      ...prev,
      occurred_from: toLocalInputValue(since),
      occurred_to: toLocalInputValue(now)
    }));
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <header className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-semibold">Message Audit Logs</h1>
        <p className="mt-2 text-sm text-slate-300">Guild ID: {guildId}</p>
        <p className="mt-1 text-sm text-slate-300">{status}</p>
      </header>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
          <div className="grid gap-1">
            <label className="text-sm text-slate-300">Event Type</label>
            <select
              value={filters.event_type}
              onChange={(e) => onFilterChange('event_type', e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
            >
              <option value="">All</option>
              <option value="edit">Edit</option>
              <option value="delete">Delete</option>
            </select>
          </div>
          <div className="grid gap-1">
            <label className="text-sm text-slate-300">Channel ID</label>
            <input
              value={filters.channel_id}
              onChange={(e) => onFilterChange('channel_id', e.target.value)}
              placeholder="Optional"
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
            />
          </div>
          <div className="grid gap-1">
            <label className="text-sm text-slate-300">Author ID</label>
            <input
              value={filters.author_id}
              onChange={(e) => onFilterChange('author_id', e.target.value)}
              placeholder="Optional"
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
            />
          </div>
          <div className="grid gap-1">
            <label className="text-sm text-slate-300">From</label>
            <input
              type="datetime-local"
              value={filters.occurred_from}
              onChange={(e) => onFilterChange('occurred_from', e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
            />
          </div>
          <div className="grid gap-1">
            <label className="text-sm text-slate-300">To</label>
            <input
              type="datetime-local"
              value={filters.occurred_to}
              onChange={(e) => onFilterChange('occurred_to', e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none ring-sky-500 focus:ring"
            />
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <button onClick={setLast24h} className="rounded-md bg-sky-700 px-3 py-2 text-sm font-medium hover:bg-sky-600">
            Last 24h
          </button>
          <button
            onClick={() => {
              setOffset(0);
              setFilters({ event_type: '', channel_id: '', author_id: '', occurred_from: '', occurred_to: '' });
            }}
            className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium hover:bg-slate-600"
          >
            Clear Filters
          </button>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-800/70 text-slate-200">
              <tr>
                <th className="px-3 py-2">When</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Channel</th>
                <th className="px-3 py-2">Author</th>
                <th className="px-3 py-2">Message ID</th>
                <th className="px-3 py-2">Old Content</th>
                <th className="px-3 py-2">New Content</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-slate-800 align-top">
                  <td className="px-3 py-2 text-slate-300">{new Date(row.occurred_at).toLocaleString()}</td>
                  <td className="px-3 py-2 text-slate-200">{row.event_type}</td>
                  <td className="px-3 py-2 text-slate-300">{row.channel_discord_id || 'unknown'}</td>
                  <td className="px-3 py-2 text-slate-300">{row.author_discord_id || 'unknown'}</td>
                  <td className="px-3 py-2 text-slate-300">{row.message_id}</td>
                  <td className="max-w-xs whitespace-pre-wrap break-words px-3 py-2 text-slate-300">{row.old_content || ''}</td>
                  <td className="max-w-xs whitespace-pre-wrap break-words px-3 py-2 text-slate-300">{row.new_content || ''}</td>
                </tr>
              ))}
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-slate-400">
                    No audit events found for current filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-300">
          Showing {rows.length === 0 ? 0 : offset + 1}-{offset + rows.length} of {total}
        </div>
        <div className="flex gap-2">
          <button
            disabled={!canPrev}
            onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
            className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>
          <button
            disabled={!canNext}
            onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
            className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

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

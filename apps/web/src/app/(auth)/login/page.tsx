"use client";

import Link from "next/link";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

export default function LoginPage() {
    const [userId, setUserId] = useState("");
    const [guildId, setGuildId] = useState("");
    const [password, setPassword] = useState("");
    const [status, setStatus] = useState<string | null>(null);

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setStatus("Logging in...");

        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ userId, guildId, password }),
        });

        if (response.ok) {
            setStatus("Success. Redirecting...");
            window.location.href = "/dashboard";
            return;
        }

        setStatus("Login failed. Check credentials and guild ID.");
    }

    return (
        <main>
            <section className="card auth-card">
                <h1>Dashboard Login</h1>
                <p className="muted-text">Use the credentials sent by the bot DM after running <code>/create-dashboard-admin</code>.</p>

                <form onSubmit={onSubmit} className="grid settings-grid">
                    <label>
                        Discord User ID
                        <input value={userId} onChange={(e) => setUserId(e.target.value)} required />
                    </label>
                    <label>
                        Guild ID
                        <input value={guildId} onChange={(e) => setGuildId(e.target.value)} required />
                    </label>
                    <label>
                        Password
                        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                    </label>
                    <button type="submit" className="btn btn-primary">Sign In</button>
                </form>

                {status ? <p className="muted-text">{status}</p> : null}
                <p><Link href="/" className="link-accent">Back to home</Link></p>
            </section>
        </main>
    );
}

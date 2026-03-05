import Link from "next/link";

export default function HomePage() {
    return (
        <main>
            <section className="card hero-card">
                <h1>Guild Command Center</h1>
                <p className="muted-text">
                    Manage moderation, automation, leveling, logging, tickets, giveaways, and analytics for each Discord server independently.
                </p>
                <div className="hero-actions">
                    <Link href="/login" className="btn btn-primary">Login</Link>
                    <Link href="/dashboard" className="btn">Open Dashboard</Link>
                </div>
            </section>
        </main>
    );
}

interface StatCardProps {
    label: string;
    value: number | string;
}

export function StatCard({ label, value }: StatCardProps) {
    return (
        <article className="card stat-card">
            <p className="stat-label">{label}</p>
            <p className="stat-value">{value}</p>
        </article>
    );
}

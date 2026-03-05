interface ModuleToggleCardProps {
    moduleKey: string;
    title?: string;
    description?: string;
    enabled: boolean;
    pending?: boolean;
    onToggle: (nextValue: boolean) => void;
}

export function ModuleToggleCard({ moduleKey, title, description, enabled, pending, onToggle }: ModuleToggleCardProps) {
    return (
        <article className="card module-card">
            <h3>{title ?? moduleKey}</h3>
            <p className="muted-text">{description ?? "No description provided."}</p>
            <p className="module-status">Status: {enabled ? "Enabled" : "Disabled"}</p>
            <button
                type="button"
                disabled={pending}
                onClick={() => onToggle(!enabled)}
                className={enabled ? "btn btn-danger" : "btn btn-success"}
            >
                {pending ? "Saving..." : enabled ? "Disable" : "Enable"}
            </button>
        </article>
    );
}

interface ModuleToggleCardProps {
    moduleKey: string;
    enabled: boolean;
    pending?: boolean;
    onToggle: (nextValue: boolean) => void;
}

export function ModuleToggleCard({ moduleKey, enabled, pending, onToggle }: ModuleToggleCardProps) {
    return (
        <article className="card module-card">
            <h3>{moduleKey}</h3>
            <p className="muted-text">Status: {enabled ? "Enabled" : "Disabled"}</p>
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

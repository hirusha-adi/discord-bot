const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API_URL}${path}`, {
        ...init,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(init?.headers ?? {}),
        },
        cache: "no-store",
    });

    if (!response.ok) {
        let message = `API error ${response.status}`;
        try {
            const payload = await response.json() as { error?: string };
            if (payload.error) {
                message = payload.error;
            }
        } catch {
            // Ignore parse errors and keep status message.
        }
        throw new Error(message);
    }

    return response.json() as Promise<T>;
}

# Stage 2 Auth Design

## Session Strategy

This project uses **JWT session tokens stored in an HttpOnly cookie**.

Why this choice for Stage 2:
- Works cleanly with the browser-based Next.js login flow.
- Keeps API auth stateless (no session table needed yet).
- Supports session persistence in browser via cookie `max_age`.

## Local Auth

- `POST /auth/local/register`: creates a local user with PBKDF2 password hash and sets session cookie.
- `POST /auth/local/login`: verifies password hash and sets session cookie.
- `GET /auth/me`: protected route, requires valid session cookie.
- `GET /protected/ping`: protected test endpoint.

## Discord OAuth

- `GET /auth/discord/login`: login redirect endpoint to Discord OAuth authorize URL.
- `GET /auth/discord/callback`: exchanges code for short-lived access token, fetches Discord user identity, sets app session cookie.
- Stored minimally in `users`: `discord_user_id`, `discord_access_token`, `discord_token_scope`, `discord_token_expires_at`.
- No refresh token is stored in Stage 2.

## OAuth Scopes

Default scopes are minimal for current and next stage needs:
- `identify`
- `guilds`

Configured via `DISCORD_OAUTH_SCOPES` (default: `identify guilds`).

Copy-Item .env.example .env -ErrorAction SilentlyContinue
Write-Host "Bootstrapped .env from .env.example if missing."
Write-Host "Install pnpm and run: pnpm install; pnpm db:generate; pnpm db:migrate"

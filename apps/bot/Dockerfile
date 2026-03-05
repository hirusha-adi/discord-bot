FROM node:20-alpine
WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-workspace.yaml ./
COPY apps/bot/package.json ./apps/bot/package.json
COPY packages/db/package.json ./packages/db/package.json

RUN pnpm install --filter @platform/bot --filter @platform/db --frozen-lockfile=false

COPY . .

CMD ["pnpm", "--filter", "@platform/bot", "dev"]

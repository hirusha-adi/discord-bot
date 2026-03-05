FROM node:20-alpine AS base
WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-workspace.yaml ./
COPY apps/api/package.json ./apps/api/package.json
COPY packages/db/package.json ./packages/db/package.json

RUN pnpm install --filter @platform/api --filter @platform/db --frozen-lockfile=false

COPY . .

EXPOSE 3001
CMD ["pnpm", "--filter", "@platform/api", "dev"]

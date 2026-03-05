FROM node:20-alpine
WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json

RUN pnpm install --filter @platform/web --frozen-lockfile=false

COPY . .

EXPOSE 3000
CMD ["pnpm", "--filter", "@platform/web", "dev"]

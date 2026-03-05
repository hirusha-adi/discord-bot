FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY app ./app
COPY next.config.js ./
COPY postcss.config.js ./
COPY tailwind.config.js ./

EXPOSE 3000

CMD ["npm", "run", "dev"]

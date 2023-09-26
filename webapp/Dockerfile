# https://johnnymetz.com/posts/dockerize-nextjs-app/
FROM node:20-alpine as build-stage
RUN npm install -g pnpm

WORKDIR /app

COPY package*.json ./
COPY pnpm-lock.yaml ./
RUN pnpm install
COPY tsconfig.json next.config.js ./
COPY src/ src/
RUN pnpm run build


FROM node:20-alpine as production-stage

LABEL org.opencontainers.image.source=https://github.com/sweeneytr/polymer
LABEL org.opencontainers.image.description="Polymer Web Server"
LABEL org.opencontainers.image.licenses=MIT

RUN npm install -g pnpm

WORKDIR /app

COPY --from=build-stage /app/.next ./.next
COPY --from=build-stage /app/node_modules ./node_modules
COPY --from=build-stage /app/package.json ./
COPY --from=build-stage /app/pnpm-lock.yaml ./
COPY --from=build-stage /app/next.config.js ./

EXPOSE 8080
ENTRYPOINT [ "pnpm", "run", "start", "--", "--port", "8080"]
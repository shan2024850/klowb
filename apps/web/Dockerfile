FROM node:24-bookworm-slim AS dependencies
WORKDIR /app
ARG BUILD_CA
RUN --mount=type=secret,id=build_ca,target=/run/secrets/build_ca NODE_EXTRA_CA_CERTS="${BUILD_CA:-/etc/ssl/certs/ca-certificates.crt}" npm install --global pnpm@10.28.0
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/types/package.json ./packages/types/
COPY apps/web/package.json ./apps/web/
RUN --mount=type=secret,id=build_ca,target=/run/secrets/build_ca NODE_EXTRA_CA_CERTS="${BUILD_CA:-/etc/ssl/certs/ca-certificates.crt}" pnpm install --frozen-lockfile
COPY --chown=node:node packages/types ./packages/types
COPY --chown=node:node apps/web ./apps/web
ENV NEXT_TELEMETRY_DISABLED=1
FROM dependencies AS development
# Local dev outputs and HMR writes belong to the unprivileged runtime user.
RUN chmod a+r package.json pnpm-workspace.yaml pnpm-lock.yaml && chmod a+rx packages apps && chown node:node /app/apps/web
USER node
CMD ["pnpm","--filter","@klowb/web","dev","--hostname","0.0.0.0"]

FROM dependencies AS build
RUN pnpm --filter @klowb/web build

FROM node:24-bookworm-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
COPY --from=build --chown=node:node /app/apps/web/.next/standalone ./
COPY --from=build --chown=node:node /app/apps/web/.next/static ./apps/web/.next/static
USER node
CMD ["node","apps/web/server.js"]

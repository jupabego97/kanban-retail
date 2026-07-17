# Build context: raíz del monorepo
# Debian/glibc (no Alpine) para native deps de Tailwind/lightningcss.

FROM node:20-bookworm-slim AS builder
WORKDIR /app

# Dependencias del monorepo (workspaces)
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages ./packages

RUN npm ci

# Código fuente del frontend
COPY apps/web ./apps/web

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1

# Ejecutar next vía node (evita fallos de PATH/.bin en workspaces)
WORKDIR /app/apps/web
RUN node ../../node_modules/next/dist/bin/next build --webpack

FROM node:20-bookworm-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs

COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs
EXPOSE 3000

CMD ["sh", "-c", "node apps/web/server.js"]

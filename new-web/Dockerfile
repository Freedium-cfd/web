# Multi-stage Bun build for SvelteKit (adapter-node).
#
#   stage 1: install + build
#   stage 2: minimal runtime image that runs `node build/`

FROM oven/bun:1.2 AS build
WORKDIR /app

# Lockfile-only install layer for cache friendliness
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

COPY . .
RUN bun run build

FROM oven/bun:1.2-slim AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=384" \
    HOST=0.0.0.0 \
    PORT=3000

# wget is needed by the HEALTHCHECK below and by the stack smoke test
# (test-stack.sh execs `wget` inside this container). bun:1.2-slim ships
# with neither wget nor curl, so install the smallest option.
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget \
    && rm -rf /var/lib/apt/lists/*

# Only the runtime artefacts. node_modules ships because adapter-node
# expects them at runtime; for a smaller image consider `bun install --production`
# in build stage and copying that instead.
COPY --from=build /app/build ./build
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

# Ownership for the working directory so the non-root user can read it
RUN chown -R bun:bun /app

EXPOSE 3000

USER bun

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000/metrics > /dev/null || exit 1

CMD ["node", "build"]

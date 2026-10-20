#!/usr/bin/env bash
# rotate-warp.sh — Zero-downtime rolling identity rotation for WGCF/WARP tunnels.
#
# Cloudflare WARP egress IPs occasionally get rate-limited or soft-blocked by
# platforms like Medium. This script cycles each WGCF container one by one,
# generating a brand-new Cloudflare WARP account & WireGuard cryptographic keypair.
#
# HAProxy load balancer (haproxy-pb) health-checks each backend slot so traffic
# seamlessly routes through remaining healthy tunnels during the rolling rotation.
set -euo pipefail
cd "$(dirname "$0")"

exec 8>/tmp/freedium-warp-rotate.lock
if ! flock -n 8; then
  echo "ERROR: another WARP rotation is already in progress; aborting." >&2
  exit 1
fi

filt="freedium-obs-wgcf"
containers=$(docker ps --filter "name=$filt" -q)
total=$(echo "$containers" | grep -v '^$' | wc -l)

if [ "$total" -lt 1 ]; then
  echo "==> No WGCF containers running. Bringing up wgcf..."
  ROTATE_IDENTITY=true docker compose up -d --scale wgcf=3 wgcf
  exit 0
fi

echo "==> Rolling identity rotation across $total WGCF tunnels (one at a time)..."

wait_healthy() {
  local target_id="$1"
  until [ "$(docker inspect -f '{{.State.Health.Status}}' "$target_id" 2>/dev/null || echo 'starting')" = "healthy" ]; do
    sleep 2
  done
}

for c in $containers; do
  name=$(docker inspect -f '{{.Name}}' "$c" | sed 's#^/##')
  echo "  -> Rotating identity for $name"

  # Remove container and its anonymous volume holding wgcf-account.toml
  docker stop "$c" >/dev/null
  docker rm -v "$c" >/dev/null

  # Respawn with fresh registration
  ROTATE_IDENTITY=true docker compose up -d --no-deps --no-recreate --scale "wgcf=$total" wgcf >/dev/null

  new_c=$(docker ps --filter "name=$filt" --latest -q)
  echo "     Waiting for $name to establish fresh WARP tunnel..."
  wait_healthy "$new_c"

  new_ip=$(docker exec "$new_c" curl -fs --max-time 5 https://api.ipify.org 2>/dev/null || echo "unknown")
  echo "     OK ($name healthy, egress IP: $new_ip)"
  sleep 3
done

echo "==> All WGCF identities successfully rotated."

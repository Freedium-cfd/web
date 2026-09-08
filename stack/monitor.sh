#!/usr/bin/env bash
# Host-level health monitor → Telegram.
#
# Deliberately INDEPENDENT of the Docker stack: a full disk or OOM can crash
# Grafana/Prometheus, so Grafana-based alerting would be down exactly when you
# need it. This is a plain cron script that keeps alerting even if the whole
# stack is down.
#
# Install (on the host):
#   1. echo 'TELEGRAM_BOT_TOKEN=...' >  /opt/freedium/monitor.env   # host-only, NOT in git
#      echo 'TELEGRAM_CHAT_ID=...'   >> /opt/freedium/monitor.env
#      chmod 600 /opt/freedium/monitor.env
#   2. crontab -e  ->  */5 * * * * /opt/freedium/stack/monitor.sh >/dev/null 2>&1
set -uo pipefail

ENV_FILE="${MONITOR_ENV:-/opt/freedium/monitor.env}"
# shellcheck disable=SC1090
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
: "${TELEGRAM_BOT_TOKEN:?set in $ENV_FILE}"
: "${TELEGRAM_CHAT_ID:?set in $ENV_FILE}"

DISK_WARN=${DISK_WARN:-80}      # % used
MEM_WARN=${MEM_WARN:-92}        # % used
RENOTIFY=${RENOTIFY:-3600}      # re-alert at most once/hour while still in alarm
# backend dropped from the fixed list: it now runs as replicas (dynamic
# names) behind Traefik. Backend health is covered by the replica check +
# the render probe below.
CRITICAL_CONTAINERS=${CRITICAL_CONTAINERS:-"freedium-mongo freedium-redis freedium-traefik"}

STATE_DIR=/var/lib/freedium-monitor
mkdir -p "$STATE_DIR"
HOST="Freedium"

tg() {
  curl -s --max-time 10 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=$1" -d "parse_mode=HTML" >/dev/null 2>&1 || true
}

# Throttled alert: (re)send at most once per RENOTIFY while the condition holds.
alert() {  # $1=key  $2=message
  local f="$STATE_DIR/$1" now; now=$(date +%s)
  if [ -f "$f" ] && [ $(( now - $(cat "$f" 2>/dev/null || echo 0) )) -lt "$RENOTIFY" ]; then
    return
  fi
  echo "$now" > "$f"
  tg "$2"
}
recover() {  # $1=key  — clears the alarm and pings once on recovery
  local f="$STATE_DIR/$1"
  if [ -f "$f" ]; then
    rm -f "$f"
    tg "✅ <b>$HOST</b> recovered: ${1}"
  fi
}

# --- disk ---
disk=$(df --output=pcent / 2>/dev/null | tail -1 | tr -dc '0-9'); disk=${disk:-0}
if [ "$disk" -ge "$DISK_WARN" ]; then
  alert disk "⚠️ <b>$HOST</b> disk <b>${disk}%</b> used (≥${DISK_WARN}%). Free space — a full disk silently breaks Mongo/backend writes (articles stop rendering)."
else
  recover disk
fi

# --- memory (disabled) ---

# --- critical single-container services ---
for c in $CRITICAL_CONTAINERS; do
  st=$(docker inspect -f '{{.State.Status}}{{if .State.Health}}/{{.State.Health.Status}}{{end}}' "$c" 2>/dev/null || echo "missing")
  case "$st" in
    running|running/healthy) recover "ct_$c" ;;
    *) alert "ct_$c" "🔴 <b>$HOST</b> <code>$c</code> is <b>$st</b>." ;;
  esac
done

# --- web tier (dynamic replica names): need >=1 healthy ---
web_ok=$(docker ps --filter name=freedium-obs-web --filter health=healthy -q 2>/dev/null | wc -l)
if [ "$web_ok" -lt 1 ]; then
  alert web "🔴 <b>$HOST</b> no healthy web replica."
else
  recover web
fi

# --- backend tier (dynamic replica names): need >=1 healthy ---
backend_ok=$(docker ps --filter name=freedium-obs-backend --filter health=healthy -q 2>/dev/null | wc -l)
if [ "$backend_ok" -lt 1 ]; then
  alert backend "🔴 <b>$HOST</b> no healthy backend replica."
else
  recover backend
fi

# --- synthetic render probe: catches "healthy but every article 500s" ---
# Containers can all report healthy (/healthz is trivial) while article
# rendering is broken (e.g. the instrumentator _IncludedRouter 500 that hid
# for 17h). Probe the real render path on a healthy backend replica directly (the
# backend image ships curl; the traefik image is FROM scratch, no shell).
PROBE_ID="${RENDER_PROBE_ID:-450a855584f8}"
probe_c=$(docker ps --filter name=freedium-obs-backend --filter health=healthy -q 2>/dev/null | head -1)
if [ -z "$probe_c" ]; then
  # Already covered by the backend replica check above
  :
else
  docker exec "$probe_c" rm -f /tmp/_probe.out 2>/dev/null || true
  if ! probe_code=$(docker exec "$probe_c" curl -s -o /tmp/_probe.out -w "%{http_code}" \
    -X POST http://localhost:7080/api/render \
    -H "content-type: application/json" \
    -d "{\"content\":\"${PROBE_ID}\"}" --max-time 30 2>/dev/null); then
    probe_code="000"
  fi
  # Clean status code: digits only, default to 000 on exec / daemon failure
  probe_code=$(echo "$probe_code" | tr -dc '0-9' | tail -c 3)
  probe_code=${probe_code:-000}

  probe_len=$(docker exec "$probe_c" sh -c 'wc -c < /tmp/_probe.out 2>/dev/null' 2>/dev/null | tr -dc '0-9')
  probe_len=${probe_len:-0}
  if [ "$probe_code" = "200" ] && [ "$probe_len" -gt 500 ]; then
    recover render
  else
    alert render "🔴 <b>$HOST</b> render path broken: /api/render → HTTP ${probe_code}, ${probe_len}B (containers may report healthy)."
  fi
fi

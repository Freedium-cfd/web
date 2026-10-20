#!/usr/bin/env bash
# Combined wgcf + microsocks entrypoint.
#
# The upstream neilpang/wgcf-docker entry.sh brings Cloudflare Warp up via
# wg-quick and then `sleep infinity`s. We start it in the background, wait
# for the `wgcf` wireguard interface to appear and start routing traffic
# through Cloudflare, then exec microsocks (SOCKS5) in the foreground so
# the container's main process is the proxy and `docker stop` is clean.
#
# microsocks doesn't have a "-b <interface>" option like dante's
# `external: wgcf`. Instead we read the wgcf interface's IPv4 address and
# pass it via `-b <ip>` so microsocks binds outbound connections to that
# source IP — forcing traffic out through the WireGuard tunnel.

set -e

# 0) Identity rotation support: if ROTATE_IDENTITY is set, wipe stale profile & account
#    files on startup so /entry.sh generates a brand-new Cloudflare WARP account & device keys.
if [ "${ROTATE_IDENTITY:-false}" = "true" ] || [ "${ROTATE_IDENTITY:-0}" = "1" ]; then
    echo "[combined-entry] ROTATE_IDENTITY active — removing old wgcf account and profile"
    rm -f /wgcf/wgcf-account.toml /wgcf/wgcf-profile.conf /etc/wireguard/wgcf.conf 2>/dev/null || true
fi

# 1) Launch upstream wgcf bootstrap in the background.
#    /entry.sh comes from neilpang/wgcf-docker and lives at the image root.
/entry.sh &
WGCF_PID=$!

# 2) Wait for the wgcf interface to be up AND for outbound traffic to be
#    going through Warp. Without this, microsocks will start before Warp is
#    ready and bind to a source IP that doesn't exist yet.
echo "[combined-entry] waiting for wgcf interface + Warp routing..."
for i in $(seq 1 120); do
    if ip link show wgcf >/dev/null 2>&1 \
       && curl -fs --max-time 3 https://www.cloudflare.com/cdn-cgi/trace 2>/dev/null \
            | grep -q -E 'warp=(on|plus)'; then
        echo "[combined-entry] Warp is up."
        break
    fi
    sleep 2
done

if ! ip link show wgcf >/dev/null 2>&1; then
    echo "[combined-entry] FATAL: wgcf interface never came up"
    exit 1
fi

# Even if the Warp trace check above timed out (some ISPs throttle WARP's
# data plane so the trace endpoint hangs), the wgcf interface exists and
# the handshake completed — microsocks can still bind to its IP. The
# compose healthcheck remains the source of truth for "fully healthy".

# 3) Read the wgcf interface's IPv4 address so we can bind outbound
#    connections to it. Retry briefly in case the address gets assigned
#    a heartbeat after the link goes up.
WGCF_IP=""
for i in $(seq 1 30); do
    WGCF_IP="$(ip -4 addr show wgcf 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1)"
    if [ -n "$WGCF_IP" ]; then
        break
    fi
    sleep 1
done

if [ -z "$WGCF_IP" ]; then
    echo "[combined-entry] FATAL: could not determine wgcf interface IPv4 address"
    exit 1
fi

echo "[combined-entry] wgcf source IP: $WGCF_IP"

# 4) Exec microsocks in the foreground.
#    -i 0.0.0.0  : listen on all interfaces inside the container
#    -p 1080     : SOCKS5 port
#    -b <ip>     : bind outbound connections to this source IP (the wgcf IP)
echo "[combined-entry] starting microsocks on :1080, outbound via $WGCF_IP"
exec /usr/local/bin/microsocks -i 0.0.0.0 -p 1080 -b "$WGCF_IP"

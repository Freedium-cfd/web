"""Tiny HTTP server exposing Prometheus /metrics for the worker process.

TaskIQ spawns child processes (worker-0, worker-1) that execute the actual
tasks — those children call JXL_CONVERSION.inc(), not the main process.
Without PROMETHEUS_MULTIPROC_DIR, each child's counters are in-memory and
invisible to the main process. With it, children write .db files to the dir
and the main process merges them via MultiProcessCollector.
"""
from __future__ import annotations

import os
import threading

from prometheus_client import CollectorRegistry, MetricsHandler, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector


def cleanup_dead_multiprocess_files(mp_dir: str) -> None:
    """Remove metrics DB files belonging to exited worker subprocesses."""
    if not mp_dir or not os.path.isdir(mp_dir):
        return
    try:
        for entry in os.scandir(mp_dir):
            if entry.is_file() and entry.name.endswith(".db"):
                parts = entry.name.rsplit(".", 1)[0].rsplit("_", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    pid = int(parts[1])
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        try:
                            os.remove(entry.path)
                        except OSError:
                            pass
    except OSError:
        pass


def start_metrics_server(port: int = 8079) -> None:
    """Start an HTTP server on `port` that serves merged multiprocess metrics.
    Runs in a daemon thread — dies when the worker process exits."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    reg = CollectorRegistry()
    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "")
    if mp_dir:
        cleanup_dead_multiprocess_files(mp_dir)
        MultiProcessCollector(reg, path=mp_dir)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/healthz":
                # Pure liveness check — never generate metrics or read multiprocess disk files
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"OK")
            elif self.path == "/metrics":
                if mp_dir:
                    cleanup_dead_multiprocess_files(mp_dir)
                data = generate_latest(reg)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, *args, **kwargs) -> None:
            pass  # suppress request logs

    server = HTTPServer(("0.0.0.0", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()


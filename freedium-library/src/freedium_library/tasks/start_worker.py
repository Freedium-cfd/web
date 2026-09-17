#!/usr/bin/env python3
"""Worker entrypoint: start the Prometheus metrics sidecar, then run the
TaskIQ worker as a child process. The sidecar stays alive and serves
/metrics. When the taskiq worker exits, the sidecar dies with it.

This avoids os.execvp (which kills the metrics thread) and the
subprocess-only approach (which couldn't forward signals properly).
"""
import os
import signal
import subprocess
import sys
import threading

from freedium_library.tasks.metrics_server import start_metrics_server

# Must start BEFORE taskiq children import prometheus_client metrics
# (the multiprocess dir switch happens at import time).
start_metrics_server()

# Let the sidecar bind before spawning children.
import time
time.sleep(0.3)

# Run the real TaskIQ worker as a subprocess. Use the same Python
# to avoid PATH issues with the taskiq console script.
# --max-tasks-per-child 200 recycles worker processes to eliminate memory leaks
# and heap fragmentation from heavy HTML/GraphQL parsing.
proc = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "taskiq",
        "worker",
        "--max-tasks-per-child",
        "200",
        "freedium_library.tasks:broker",
    ],
)

# Forward signals so docker stop / SIGTERM reaches the child.
def _forward(signum, frame):
    proc.send_signal(signum)
signal.signal(signal.SIGTERM, _forward)
signal.signal(signal.SIGINT, _forward)

rc = proc.wait()
sys.exit(rc)


# ═══════════════════════════════════════════
# Evently — Gunicorn Configuration
# ═══════════════════════════════════════════

import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker Processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "evently-api"

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Server Mechanics
preload_app = True
daemon = False
tmp_upload_dir = None

# Hooks
def on_starting(server):
    server.log.info("Evently API starting...")

def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers.")

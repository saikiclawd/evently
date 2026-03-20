# ═══════════════════════════════════════════
# Evently — Gunicorn Configuration
# ═══════════════════════════════════════════

import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:5000"

# Worker Processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Process Naming
proc_name = "evently-api"

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

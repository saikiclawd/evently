# ═══════════════════════════════════════════
# FloraFlow — Gunicorn Configuration
# Monolithic: serves React SPA + API on :5001
# ═══════════════════════════════════════════

import multiprocessing
import os

# Server socket — single port, nginx handles SSL in front
bind = "127.0.0.1:5001"

# Workers: (2 × cores) + 1 is the standard recommendation
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
timeout = 120          # extra time for AI image analysis calls
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/opt/evently/logs/gunicorn-access.log"
errorlog  = "/opt/evently/logs/gunicorn-error.log"
loglevel  = os.getenv("LOG_LEVEL", "info").lower()

# Process naming (visible in ps/top)
proc_name = "floraflow"

# Security
limit_request_line       = 8190
limit_request_fields     = 100
limit_request_field_size = 8190

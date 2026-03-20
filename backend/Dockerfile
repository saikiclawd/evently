# ═══════════════════════════════════════════
# EventFlow Pro — Flask API Dockerfile
# ═══════════════════════════════════════════
# Multi-stage build for minimal production image

# ── Stage 1: Build dependencies ──
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production image ──
FROM python:3.12-slim AS production

# Security: run as non-root
RUN groupadd -r eventflow && useradd -r -g eventflow -d /app -s /sbin/nologin eventflow

# System deps for psycopg2 and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libjpeg62-turbo libwebp7 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY . .

# Set ownership
RUN chown -R eventflow:eventflow /app

USER eventflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]

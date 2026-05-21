#!/usr/bin/env bash
# ═══════════════════════════════════════════
# FloraFlow — Deploy Script
# ═══════════════════════════════════════════
# Run as the deploy user on the Linode.
# Usage: bash scripts/deploy.sh [--no-migrate] [--restart-only]

set -euo pipefail

APP_DIR="/opt/evently"
VENV="${APP_DIR}/.venv"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"; }
err()  { echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"; exit 1; }

SKIP_MIGRATE=false
RESTART_ONLY=false

for arg in "$@"; do
    case $arg in
        --no-migrate)   SKIP_MIGRATE=true ;;
        --restart-only) RESTART_ONLY=true ;;
    esac
done

echo ""
echo "═══════════════════════════════════════════"
echo "  FloraFlow — Deploying"
echo "═══════════════════════════════════════════"
echo ""

cd "$APP_DIR"

if [ "$RESTART_ONLY" = false ]; then
    # ── Pull latest code ──
    log "Pulling latest code..."
    git fetch origin main
    git reset --hard origin/main
    log "Code updated ($(git rev-parse --short HEAD))"

    # ── Update Python dependencies ──
    log "Installing Python dependencies..."
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r backend/requirements.txt
    log "Python deps up to date"

    # ── Build React frontend ──
    log "Building frontend..."
    cd "$APP_DIR/frontend"
    npm ci --prefer-offline --silent
    npm run build
    cd "$APP_DIR"
    log "Frontend built"
fi

# ── Database migrations ──
if [ "$SKIP_MIGRATE" = false ]; then
    log "Running database migrations..."
    set -a; source "$APP_DIR/.env"; set +a
    FLASK_APP=backend/app:create_app "$VENV/bin/flask" db upgrade
    log "Migrations applied"
fi

# ── Reload gunicorn (zero-downtime) ──
log "Reloading gunicorn..."
if systemctl is-active --quiet floraflow; then
    # SIGHUP causes gunicorn to reload workers without dropping connections
    systemctl kill -s HUP floraflow
    sleep 3
else
    systemctl start floraflow
    sleep 3
fi

# ── Health check ──
echo ""
if curl -sf http://127.0.0.1:5001/api/v1/health > /dev/null 2>&1; then
    log "Health check: ✅ OK"
else
    warn "Health check: ⚠️  /api/v1/health not responding (app may still be warming up)"
fi

echo ""
log "Deploy complete — $(git rev-parse --short HEAD)"
echo ""
systemctl status floraflow --no-pager --lines=5

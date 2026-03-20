#!/usr/bin/env bash
# ═══════════════════════════════════════════
# EventFlow Pro — Manual Deployment Script
# ═══════════════════════════════════════════
# Usage: bash scripts/deploy.sh [--no-migrate] [--restart-only]

set -euo pipefail

APP_DIR="/opt/eventflow"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"; }

SKIP_MIGRATE=false
RESTART_ONLY=false

for arg in "$@"; do
    case $arg in
        --no-migrate)  SKIP_MIGRATE=true ;;
        --restart-only) RESTART_ONLY=true ;;
    esac
done

echo ""
echo "═══════════════════════════════════════════"
echo "  EventFlow Pro — Deploying..."
echo "═══════════════════════════════════════════"
echo ""

cd "$APP_DIR"

if [ "$RESTART_ONLY" = false ]; then
    # Pull latest code
    log "Pulling latest code..."
    git pull origin main

    # Build images
    log "Building Docker images..."
    $COMPOSE build --parallel
fi

# Database migration
if [ "$SKIP_MIGRATE" = false ]; then
    log "Running database migrations..."
    $COMPOSE run --rm api flask db upgrade
fi

# Rolling restart: API instances
log "Restarting API instance 1..."
$COMPOSE up -d --no-deps --force-recreate api
sleep 8

# Health check API 1
if curl -sf http://localhost:8500/api/v1/health > /dev/null; then
    log "API instance 1 healthy ✓"
else
    warn "API instance 1 health check failed — continuing..."
fi

log "Restarting API instance 2..."
$COMPOSE up -d --no-deps --force-recreate api-2
sleep 5

# Restart remaining services
log "Restarting workers and frontend..."
$COMPOSE up -d --remove-orphans

# Cleanup
log "Cleaning up old images..."
docker image prune -f > /dev/null 2>&1

# Final health check
sleep 5
echo ""
if curl -sf http://localhost:8500/api/v1/health > /dev/null; then
    log "API: ✅ Healthy"
else
    warn "API: ⚠️  Not responding"
fi

if curl -sf http://localhost:8600/ > /dev/null; then
    log "Frontend: ✅ Healthy"
else
    warn "Frontend: ⚠️  Not responding"
fi

echo ""
log "Deployment complete!"
echo ""

# Show running containers
$COMPOSE ps

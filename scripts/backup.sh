#!/usr/bin/env bash
# ═══════════════════════════════════════════
# EventFlow Pro — Database Backup Script
# ═══════════════════════════════════════════
# Runs daily via cron. Backs up PostgreSQL to local + S3.

set -euo pipefail

BACKUP_DIR="/opt/eventflow/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="eventflow_${TIMESTAMP}.sql.gz"

# Source .env for credentials
set -a
source /opt/eventflow/.env
set +a

echo "[$(date)] Starting backup..."

# Dump database via Docker
docker compose -f /opt/eventflow/docker-compose.yml \
    -f /opt/eventflow/docker-compose.prod.yml \
    exec -T postgres pg_dump \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=custom \
    --compress=9 \
    | gzip > "${BACKUP_DIR}/${FILENAME}"

FILESIZE=$(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)
echo "[$(date)] Local backup created: ${FILENAME} (${FILESIZE})"

# Upload to Linode Object Storage (S3-compatible) if configured
if [ -n "${S3_ENDPOINT:-}" ] && [ -n "${S3_ACCESS_KEY:-}" ]; then
    # Install s3cmd if not present
    if ! command -v s3cmd &> /dev/null; then
        apt-get install -y s3cmd > /dev/null 2>&1
    fi

    s3cmd put "${BACKUP_DIR}/${FILENAME}" \
        "s3://${S3_BUCKET}/backups/${FILENAME}" \
        --host="${S3_ENDPOINT##https://}" \
        --host-bucket="%(bucket)s.${S3_ENDPOINT##https://}" \
        --access_key="${S3_ACCESS_KEY}" \
        --secret_key="${S3_SECRET_KEY}" \
        --region="${S3_REGION:-us-east-1}" \
        --no-mime-magic \
        2>/dev/null && \
    echo "[$(date)] Uploaded to S3: s3://${S3_BUCKET}/backups/${FILENAME}" || \
    echo "[$(date)] WARNING: S3 upload failed — local backup preserved"
fi

# Cleanup local backups older than 7 days
find "${BACKUP_DIR}" -name "eventflow_*.sql.gz" -mtime +7 -delete
echo "[$(date)] Cleaned up old local backups"

echo "[$(date)] Backup complete."

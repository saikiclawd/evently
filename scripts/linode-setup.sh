#!/usr/bin/env bash
# ═══════════════════════════════════════════
# FloraFlow — Akamai Linode Server Setup
# ═══════════════════════════════════════════
# Run as root on a fresh Ubuntu 24.04 LTS Linode.
# Usage: bash linode-setup.sh
#
# Recommended plan: Dedicated 4GB ($36/mo)
#   4 GB RAM | 2 vCPU | 80 GB SSD | 4 TB Transfer
#
# Architecture: monolithic gunicorn
#   Nginx (SSL) → gunicorn :5001 (Flask serves React + API)
#   PostgreSQL on same host, no Docker, no Redis
# ═══════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[→]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "═══════════════════════════════════════════"
echo "  FloraFlow — Akamai Linode Setup"
echo "═══════════════════════════════════════════"
echo ""

[ "$(id -u)" -ne 0 ] && err "Run as root"

# ── Prompt for configuration ──
read -rp "Domain (e.g. app.yourdomain.com): "          DOMAIN
read -rp "Email for Let's Encrypt SSL: "               SSL_EMAIL
read -rp "GitHub repo URL (https://github.com/...): "  REPO_URL
read -rp "Groq API key (gsk_...): "                    GROQ_API_KEY
echo ""
info "Domain:   $DOMAIN"
info "SSL Email: $SSL_EMAIL"
info "Repo:     $REPO_URL"
echo ""
read -rp "Proceed? (y/N): " CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || exit 0

# ══════════════════════════════════════════
# PHASE 1: System Hardening
# ══════════════════════════════════════════
info "Phase 1: System hardening..."

apt-get update && apt-get upgrade -y
timedatectl set-timezone UTC

apt-get install -y \
    curl wget git ufw fail2ban unattended-upgrades \
    apt-transport-https ca-certificates gnupg lsb-release \
    htop ncdu tree jq build-essential
log "Essential packages installed"

# Deploy user
if ! id -u deploy &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
    echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy
    chmod 440 /etc/sudoers.d/deploy
    mkdir -p /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    chmod 600 /home/deploy/.ssh/authorized_keys
    log "Deploy user created"
else
    log "Deploy user already exists"
fi

# Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log "UFW firewall: SSH / HTTP / HTTPS"

# Fail2ban
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3
bantime  = 86400
EOF
systemctl enable fail2ban
systemctl restart fail2ban
log "Fail2ban configured"

# SSH hardening
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/'  /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/'                         /etc/ssh/sshd_config
systemctl restart ssh 2>/dev/null || systemctl restart sshd || true
log "SSH hardened (key-only login)"

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
log "Automatic security updates enabled"

# ══════════════════════════════════════════
# PHASE 2: Python 3.12
# ══════════════════════════════════════════
info "Phase 2: Installing Python 3.12..."

add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.12 python3.12-venv python3.12-dev python3.12-distutils
# pip for 3.12
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
log "Python 3.12 installed ($(python3.12 --version))"

# ══════════════════════════════════════════
# PHASE 3: PostgreSQL
# ══════════════════════════════════════════
info "Phase 3: Installing PostgreSQL..."

apt-get install -y postgresql postgresql-contrib libpq-dev
systemctl enable postgresql
systemctl start postgresql
log "PostgreSQL installed"

# Generate secure DB password
DB_PASS=$(openssl rand -hex 20)

sudo -u postgres psql <<SQL
CREATE USER floraflow WITH PASSWORD '${DB_PASS}';
CREATE DATABASE floraflow OWNER floraflow;
GRANT ALL PRIVILEGES ON DATABASE floraflow TO floraflow;
SQL
log "PostgreSQL database and user created"

# ══════════════════════════════════════════
# PHASE 4: Nginx + Certbot
# ══════════════════════════════════════════
info "Phase 4: Installing Nginx and Certbot..."

apt-get install -y nginx certbot python3-certbot-nginx
systemctl enable nginx
log "Nginx installed"

# ══════════════════════════════════════════
# PHASE 5: Clone Repository
# ══════════════════════════════════════════
info "Phase 5: Cloning repository..."

if [ ! -d "/opt/evently/.git" ]; then
    rm -rf /opt/evently
    git clone "$REPO_URL" /opt/evently
    log "Repository cloned"
else
    cd /opt/evently && git pull origin main
    log "Repository updated"
fi

mkdir -p /opt/evently/{logs,backups}
chown -R deploy:deploy /opt/evently
log "App directory ready at /opt/evently"

# ══════════════════════════════════════════
# PHASE 6: Python Virtual Environment
# ══════════════════════════════════════════
info "Phase 6: Setting up Python venv..."

cd /opt/evently
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt

# Node / npm for the one-time frontend build
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

cd /opt/evently/frontend
npm ci --prefer-offline
npm run build
log "Frontend built to frontend/dist/"

chown -R deploy:deploy /opt/evently
log "Python venv and frontend ready"

# ══════════════════════════════════════════
# PHASE 7: Environment File
# ══════════════════════════════════════════
info "Phase 7: Writing .env..."

SECRET=$(openssl rand -hex 32)

cat > /opt/evently/.env <<EOF
# ── App ──
FLASK_ENV=production
FLASK_CONFIG=production
SECRET_KEY=${SECRET}
APP_DOMAIN=${DOMAIN}
FRONTEND_URL=https://${DOMAIN}
SERVE_STATIC=1

# ── Database ──
DATABASE_URL=postgresql://floraflow:${DB_PASS}@127.0.0.1:5432/floraflow

# ── Groq (AI Stem Analyzer) ──
GROQ_API_KEY=${GROQ_API_KEY}

# ── Logging ──
LOG_LEVEL=info
EOF

chmod 600 /opt/evently/.env
chown deploy:deploy /opt/evently/.env
log ".env written (chmod 600)"

warn "Additional optional keys — edit /opt/evently/.env to add:"
warn "  STRIPE_SECRET_KEY, SENDGRID_API_KEY, GOOGLE_CLIENT_ID, etc."

# ══════════════════════════════════════════
# PHASE 8: Database Migration
# ══════════════════════════════════════════
info "Phase 8: Running database migrations..."

cd /opt/evently
set -a; source .env; set +a
FLASK_APP=backend/app:create_app .venv/bin/flask db upgrade
log "Database migrations applied"

# ══════════════════════════════════════════
# PHASE 9: Systemd Service
# ══════════════════════════════════════════
info "Phase 9: Installing systemd service..."

cp /opt/evently/floraflow.service /etc/systemd/system/floraflow.service
systemctl daemon-reload
systemctl enable floraflow
systemctl start floraflow
sleep 3

if systemctl is-active --quiet floraflow; then
    log "floraflow service running"
else
    warn "floraflow service failed to start — check: journalctl -u floraflow -n 50"
fi

# ══════════════════════════════════════════
# PHASE 10: SSL Certificate
# ══════════════════════════════════════════
info "Phase 10: Obtaining SSL certificate..."

# Temporary HTTP-only nginx to pass ACME challenge
cat > /etc/nginx/sites-available/floraflow-temp <<NGXEOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 200 'FloraFlow — setting up SSL...'; add_header Content-Type text/plain; }
}
NGXEOF

mkdir -p /var/www/certbot
ln -sf /etc/nginx/sites-available/floraflow-temp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

certbot certonly --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$SSL_EMAIL" \
    --agree-tos \
    --non-interactive
log "SSL certificate issued for $DOMAIN"

# SSL auto-renewal
cat > /etc/cron.d/certbot-renew <<'EOF'
0 3 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

# ══════════════════════════════════════════
# PHASE 11: Nginx Production Config
# ══════════════════════════════════════════
info "Phase 11: Deploying Nginx config..."

cp /opt/evently/nginx/evently.conf /etc/nginx/sites-available/floraflow
sed -i "s/evently.yourdomain.com/${DOMAIN}/g" /etc/nginx/sites-available/floraflow

ln -sf /etc/nginx/sites-available/floraflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/floraflow-temp
rm -f /etc/nginx/sites-available/floraflow-temp
nginx -t && systemctl reload nginx
log "Nginx production config active"

# ══════════════════════════════════════════
# PHASE 12: Backup Cron
# ══════════════════════════════════════════
info "Phase 12: Setting up database backups..."

cat > /opt/evently/scripts/pg-backup.sh <<'BKEOF'
#!/usr/bin/env bash
# Daily PostgreSQL backup — runs as deploy user
set -euo pipefail
BACKUP_DIR="/opt/evently/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U floraflow -h 127.0.0.1 floraflow | gzip > "${BACKUP_DIR}/floraflow_${DATE}.sql.gz"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
BKEOF
chmod +x /opt/evently/scripts/pg-backup.sh
chown deploy:deploy /opt/evently/scripts/pg-backup.sh

cat > /etc/cron.d/floraflow-backup <<EOF
0 2 * * * deploy PGPASSWORD='${DB_PASS}' /opt/evently/scripts/pg-backup.sh >> /opt/evently/logs/backup.log 2>&1
EOF
log "Daily backup cron configured (2 AM UTC)"

# ══════════════════════════════════════════
# PHASE 13: Kernel Tuning
# ══════════════════════════════════════════
info "Phase 13: Kernel tuning..."

cat >> /etc/sysctl.conf <<'EOF'

# ── FloraFlow Performance ──
net.core.somaxconn            = 65535
net.core.netdev_max_backlog   = 65535
net.ipv4.tcp_max_syn_backlog  = 65535
net.ipv4.tcp_fin_timeout      = 10
net.ipv4.tcp_tw_reuse         = 1
net.ipv4.ip_local_port_range  = 1024 65535
vm.swappiness                 = 10
fs.file-max                   = 2097152
EOF

sysctl -p
log "Kernel parameters applied"

# Logrotate
cat > /etc/logrotate.d/floraflow <<'EOF'
/opt/evently/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    postrotate
        systemctl kill -s USR1 floraflow 2>/dev/null || true
    endscript
}
EOF
log "Log rotation configured"

# ══════════════════════════════════════════
# DONE
# ══════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════"
echo -e "  ${GREEN}FloraFlow — Setup Complete!${NC}"
echo "═══════════════════════════════════════════"
echo ""
echo "  Server IP : $(curl -s ifconfig.me 2>/dev/null || echo 'run: curl ifconfig.me')"
echo "  App URL   : https://${DOMAIN}"
echo ""
echo "  Service commands:"
echo "    systemctl status floraflow"
echo "    systemctl restart floraflow"
echo "    journalctl -u floraflow -f"
echo ""
echo "  Deploy updates:"
echo "    bash /opt/evently/scripts/deploy.sh"
echo ""
echo "  Edit environment (API keys):"
echo "    nano /opt/evently/.env && systemctl restart floraflow"
echo ""
echo "  PostgreSQL DB password saved in /opt/evently/.env"
echo ""
echo "═══════════════════════════════════════════"

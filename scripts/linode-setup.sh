#!/usr/bin/env bash
# ═══════════════════════════════════════════
# EventFlow Pro — Linode Server Setup Script
# ═══════════════════════════════════════════
# Run as root on a fresh Ubuntu 24.04 Linode
# Usage: bash linode-setup.sh
#
# Recommended plan: Dedicated 4GB ($36/mo)
#   4 GB RAM | 2 CPU Cores | 80 GB SSD | 4 TB Transfer
# ═══════════════════════════════════════════

set -euo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[→]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "═══════════════════════════════════════════"
echo "  EventFlow Pro — Linode Server Setup"
echo "═══════════════════════════════════════════"
echo ""

# ── Validate running as root ──
if [ "$(id -u)" -ne 0 ]; then
    err "This script must be run as root"
fi

# ── Prompt for configuration ──
read -rp "Enter your domain (e.g., eventflow.yourdomain.com): " DOMAIN
read -rp "Enter your email for Let's Encrypt SSL: " SSL_EMAIL
read -rp "Enter GitHub repo URL (e.g., https://github.com/org/eventflow-pro.git): " REPO_URL

info "Domain: $DOMAIN"
info "SSL Email: $SSL_EMAIL"
info "Repo: $REPO_URL"
echo ""
read -rp "Proceed? (y/N): " CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || exit 0

# ══════════════════════════════════════════
# PHASE 1: System Hardening
# ══════════════════════════════════════════
info "Phase 1: System hardening..."

# Update system
apt-get update && apt-get upgrade -y
log "System updated"

# Set timezone
timedatectl set-timezone UTC
log "Timezone set to UTC"

# Install essentials
apt-get install -y \
    curl wget git ufw fail2ban unattended-upgrades \
    apt-transport-https ca-certificates gnupg lsb-release \
    htop ncdu tree jq
log "Essential packages installed"

# ── Create deploy user ──
if ! id -u deploy &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
    echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy
    chmod 440 /etc/sudoers.d/deploy

    # Copy SSH keys from root
    mkdir -p /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    chmod 600 /home/deploy/.ssh/authorized_keys
    log "Deploy user created with SSH access"
else
    log "Deploy user already exists"
fi

# ── Firewall ──
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw --force enable
log "Firewall configured (SSH, HTTP, HTTPS)"

# ── Fail2ban ──
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
EOF
systemctl enable fail2ban
systemctl restart fail2ban
log "Fail2ban configured"

# ── SSH hardening ──
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/' /etc/ssh/sshd_config
systemctl restart ssh || systemctl restart sshd || true
log "SSH hardened"

# ── Auto security updates ──
cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
log "Automatic security updates enabled"

# ══════════════════════════════════════════
# PHASE 2: Docker Installation
# ══════════════════════════════════════════
info "Phase 2: Installing Docker..."

# Docker official repo
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin

# Add deploy user to docker group
usermod -aG docker deploy

# Docker daemon config
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}
EOF

systemctl enable docker
systemctl restart docker
log "Docker installed and configured"

# ══════════════════════════════════════════
# PHASE 3: Nginx Installation
# ══════════════════════════════════════════
info "Phase 3: Installing Nginx..."

apt-get install -y nginx certbot python3-certbot-nginx
systemctl enable nginx
log "Nginx installed"

# ══════════════════════════════════════════
# PHASE 4: Application Setup
# ══════════════════════════════════════════
info "Phase 4: Setting up application..."

# Create directory structure
mkdir -p /var/www/certbot

# Clone repository
if [ ! -d "/opt/eventflow/.git" ]; then
    rm -rf /opt/eventflow
    mkdir -p /opt/eventflow
    git clone "$REPO_URL" /opt/eventflow
    log "Repository cloned"
else
    cd /opt/eventflow
    git pull origin main
    log "Repository updated"
fi

# Create data dirs AFTER cloning
mkdir -p /opt/eventflow/data/{postgres,redis}
mkdir -p /opt/eventflow/backups
mkdir -p /opt/eventflow/logs

# Set ownership
chown -R deploy:deploy /opt/eventflow
log "Application directory created at /opt/eventflow"

# ══════════════════════════════════════════
# PHASE 5: SSL Certificate
# ══════════════════════════════════════════
info "Phase 5: Setting up SSL..."

# Temporary nginx config for certbot challenge
cat > /etc/nginx/sites-available/eventflow-temp <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'EventFlow Pro - Setting up...';
        add_header Content-Type text/plain;
    }
}
EOF

ln -sf /etc/nginx/sites-available/eventflow-temp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Get certificate
certbot certonly --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$SSL_EMAIL" \
    --agree-tos \
    --non-interactive
log "SSL certificate obtained"

# Auto-renewal cron
cat > /etc/cron.d/certbot-renew <<'EOF'
0 3 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
log "SSL auto-renewal configured"

# ══════════════════════════════════════════
# PHASE 6: Nginx Production Config
# ══════════════════════════════════════════
info "Phase 6: Configuring Nginx reverse proxy..."

# Copy and customize the production Nginx config
cp /opt/eventflow/nginx/eventflow.conf /etc/nginx/sites-available/eventflow
sed -i "s/eventflow.yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/eventflow

ln -sf /etc/nginx/sites-available/eventflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/eventflow-temp
rm -f /etc/nginx/sites-available/eventflow-temp

nginx -t && systemctl reload nginx
log "Nginx production config deployed"

# ══════════════════════════════════════════
# PHASE 7: Environment & First Deploy
# ══════════════════════════════════════════
info "Phase 7: Environment setup..."

cd /opt/eventflow

if [ ! -f ".env" ]; then
    cp .env.example .env
    # Generate random secret key
    SECRET=$(openssl rand -hex 32)
    sed -i "s/CHANGE_ME_TO_RANDOM_64_CHAR_STRING/$SECRET/" .env
    # Generate random DB password
    DB_PASS=$(openssl rand -hex 16)
    sed -i "s/CHANGE_ME_STRONG_PASSWORD/$DB_PASS/g" .env
    sed -i "s/eventflow.yourdomain.com/$DOMAIN/g" .env
    warn ".env file created — EDIT IT with your API keys before first deploy!"
    warn "  nano /opt/eventflow/.env"
else
    log ".env already exists"
fi

# ══════════════════════════════════════════
# PHASE 8: Backup Cron
# ══════════════════════════════════════════
info "Phase 8: Setting up backups..."

cp /opt/eventflow/scripts/backup.sh /opt/eventflow/backups/
chmod +x /opt/eventflow/backups/backup.sh

cat > /etc/cron.d/eventflow-backup <<EOF
# Daily database backup at 2 AM UTC
0 2 * * * deploy /opt/eventflow/backups/backup.sh >> /opt/eventflow/logs/backup.log 2>&1
# Weekly cleanup of backups older than 30 days
0 3 * * 0 deploy find /opt/eventflow/backups/ -name "*.sql.gz" -mtime +30 -delete
EOF
log "Daily backup cron configured"

# ══════════════════════════════════════════
# PHASE 9: Kernel Tuning
# ══════════════════════════════════════════
info "Phase 9: Kernel tuning..."

cat >> /etc/sysctl.conf <<'EOF'

# ── EventFlow Pro — Performance Tuning ──
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535
vm.swappiness = 10
vm.overcommit_memory = 1
fs.file-max = 2097152
EOF

sysctl -p
log "Kernel parameters tuned"

# ══════════════════════════════════════════
# PHASE 10: Logrotate
# ══════════════════════════════════════════
cat > /etc/logrotate.d/eventflow <<'EOF'
/opt/eventflow/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
}
EOF
log "Log rotation configured"

# ══════════════════════════════════════════
# DONE
# ══════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════"
echo -e "  ${GREEN}Server Setup Complete!${NC}"
echo "═══════════════════════════════════════════"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Edit environment variables:"
echo "     nano /opt/eventflow/.env"
echo ""
echo "  2. Start the application:"
echo "     cd /opt/eventflow"
echo "     docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo "  3. Run initial database migration:"
echo "     docker compose exec api flask db upgrade"
echo ""
echo "  4. Set up GitHub Secrets for CI/CD:"
echo "     LINODE_HOST     = $(curl -s ifconfig.me)"
echo "     DEPLOY_USER     = deploy"
echo "     SSH_PRIVATE_KEY  = (your deploy SSH key)"
echo "     SSH_PORT         = 22"
echo ""
echo "  5. Push to main branch to auto-deploy!"
echo ""
echo "  Your app will be live at: https://$DOMAIN"
echo ""
echo "═══════════════════════════════════════════"

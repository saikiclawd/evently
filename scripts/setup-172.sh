#!/usr/bin/env bash
# ═══════════════════════════════════════════
# EventFlow Pro — Linode Setup (IP-only)
# Server: 172.105.18.229
# ═══════════════════════════════════════════
# Run as root: bash setup-172.sh

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[→]${NC} $1"; }

LINODE_IP="172.105.18.229"
REPO_URL="https://github.com/saikiclawd/evently.git"

echo ""
echo "═══════════════════════════════════════════"
echo "  EventFlow Pro — Server Setup"
echo "  IP: $LINODE_IP"
echo "═══════════════════════════════════════════"
echo ""

[ "$(id -u)" -ne 0 ] && { echo "Run as root!"; exit 1; }

# ══════════════════════════════════════════
# PHASE 1: System Update & Hardening
# ══════════════════════════════════════════
info "Phase 1: System hardening..."

apt-get update && apt-get upgrade -y
timedatectl set-timezone UTC

apt-get install -y \
    curl wget git ufw fail2ban unattended-upgrades \
    apt-transport-https ca-certificates gnupg lsb-release \
    htop ncdu tree jq
log "Packages installed"

# Create deploy user
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
ufw --force enable
log "Firewall configured (SSH + HTTP)"

# Fail2ban
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
EOF
systemctl enable fail2ban
systemctl restart fail2ban
log "Fail2ban configured"

# SSH hardening
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
log "SSH hardened"

# Auto security updates
cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
log "Auto-updates enabled"

# ══════════════════════════════════════════
# PHASE 2: Docker
# ══════════════════════════════════════════
info "Phase 2: Installing Docker..."

if ! command -v docker &>/dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin
fi

usermod -aG docker deploy

mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "50m", "max-file": "5" },
  "storage-driver": "overlay2",
  "live-restore": true
}
EOF
systemctl enable docker
systemctl restart docker
log "Docker installed"

# ══════════════════════════════════════════
# PHASE 3: Nginx
# ══════════════════════════════════════════
info "Phase 3: Installing Nginx..."

apt-get install -y nginx
systemctl enable nginx
log "Nginx installed"

# ══════════════════════════════════════════
# PHASE 4: Clone App
# ══════════════════════════════════════════
info "Phase 4: Setting up application..."

mkdir -p /opt/eventflow/data/{postgres,redis}
mkdir -p /opt/eventflow/backups
mkdir -p /opt/eventflow/logs

cd /opt/eventflow
if [ ! -d ".git" ]; then
    git clone "$REPO_URL" .
    log "Repository cloned"
else
    git pull origin main
    log "Repository updated"
fi

chown -R deploy:deploy /opt/eventflow
log "App at /opt/eventflow"

# ══════════════════════════════════════════
# PHASE 5: Nginx Config (IP-only, no SSL)
# ══════════════════════════════════════════
info "Phase 5: Configuring Nginx..."

cp /opt/eventflow/nginx/eventflow-ip.conf /etc/nginx/sites-available/eventflow
ln -sf /etc/nginx/sites-available/eventflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
log "Nginx configured for http://$LINODE_IP"

# ══════════════════════════════════════════
# PHASE 6: Environment File
# ══════════════════════════════════════════
info "Phase 6: Environment setup..."

cd /opt/eventflow
if [ ! -f ".env" ]; then
    cp .env.example .env
    SECRET=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 16)
    sed -i "s/CHANGE_ME_TO_RANDOM_64_CHAR_STRING/$SECRET/" .env
    sed -i "s/CHANGE_ME_STRONG_PASSWORD/$DB_PASS/g" .env
    sed -i "s/eventflow.yourdomain.com/$LINODE_IP/g" .env
    sed -i "s|FRONTEND_URL=https://eventflow.yourdomain.com|FRONTEND_URL=http://$LINODE_IP|g" .env
    warn ".env created with auto-generated secrets"
    warn "  Edit API keys later: nano /opt/eventflow/.env"
else
    log ".env already exists"
fi

# ══════════════════════════════════════════
# PHASE 7: Backup Cron
# ══════════════════════════════════════════
info "Phase 7: Backups..."

chmod +x /opt/eventflow/scripts/backup.sh
cat > /etc/cron.d/eventflow-backup <<EOF
0 2 * * * deploy /opt/eventflow/scripts/backup.sh >> /opt/eventflow/logs/backup.log 2>&1
0 3 * * 0 deploy find /opt/eventflow/backups/ -name "*.sql.gz" -mtime +30 -delete
EOF
log "Daily backup cron set"

# ══════════════════════════════════════════
# PHASE 8: Kernel Tuning
# ══════════════════════════════════════════
info "Phase 8: Kernel tuning..."

if ! grep -q "EventFlow" /etc/sysctl.conf; then
cat >> /etc/sysctl.conf <<'EOF'

# ── EventFlow Pro ──
net.core.somaxconn = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
vm.swappiness = 10
vm.overcommit_memory = 1
fs.file-max = 2097152
EOF
sysctl -p > /dev/null 2>&1
fi
log "Kernel tuned"

# ══════════════════════════════════════════
# PHASE 9: Start the Application
# ══════════════════════════════════════════
info "Phase 9: Starting the application stack..."

cd /opt/eventflow

# Build and start
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build 2>&1 | tail -5

# Wait for services
echo "Waiting for services to start..."
sleep 15

# Health check
if curl -sf http://localhost:5000/api/v1/health > /dev/null 2>&1; then
    log "API: healthy ✅"
else
    warn "API: not responding yet (may need a moment)"
fi

if curl -sf http://localhost:3000/ > /dev/null 2>&1; then
    log "Frontend: healthy ✅"
else
    warn "Frontend: not responding yet (may need a moment)"
fi

# ══════════════════════════════════════════
# DONE
# ══════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════"
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "═══════════════════════════════════════════"
echo ""
echo "  Your app is at: http://$LINODE_IP"
echo ""
echo "  GitHub Secrets needed:"
echo "    LINODE_HOST      = $LINODE_IP"
echo "    DEPLOY_USER      = deploy"
echo "    SSH_PRIVATE_KEY   = (your ~/.ssh/evently_deploy key)"
echo "    SSH_PORT          = 22"
echo ""
echo "  Next steps:"
echo "    1. Add the 4 GitHub Secrets above"
echo "    2. Edit API keys:  ssh deploy@$LINODE_IP 'nano /opt/eventflow/.env'"
echo "    3. Push to main to auto-deploy!"
echo ""
echo "  Useful commands:"
echo "    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "    docker compose -f docker-compose.yml -f docker-compose.prod.yml ps"
echo ""
echo "═══════════════════════════════════════════"

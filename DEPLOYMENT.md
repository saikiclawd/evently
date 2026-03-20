# EventFlow Pro — Deployment Guide

> Complete step-by-step guide to deploy on Akamai Linode with GitHub Actions CI/CD

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Provision Linode Server](#2-provision-linode-server)
3. [DNS Configuration](#3-dns-configuration)
4. [SSH Key Setup](#4-ssh-key-setup)
5. [Server Setup (Automated)](#5-server-setup-automated)
6. [GitHub Repository Setup](#6-github-repository-setup)
7. [GitHub Secrets Configuration](#7-github-secrets-configuration)
8. [First Deployment](#8-first-deployment)
9. [Ongoing Deployments (CI/CD)](#9-ongoing-deployments-cicd)
10. [Monitoring & Maintenance](#10-monitoring--maintenance)
11. [Troubleshooting](#11-troubleshooting)
12. [Cost Breakdown](#12-cost-breakdown)

---

## 1. Prerequisites

Before you begin, ensure you have:

- An Akamai / Linode account (sign up at cloud.linode.com)
- A GitHub account with the repository created
- A registered domain name
- API keys ready for: Stripe, SendGrid, Google Cloud, DocuSign (optional)
- SSH client on your local machine

---

## 2. Provision Linode Server

### Via Linode Cloud Manager

1. Log in to **cloud.linode.com**
2. Click **Create Linode**
3. Choose these settings:

| Setting | Recommended Value |
|---------|------------------|
| Image | Ubuntu 24.04 LTS |
| Region | Closest to your customers (e.g., Newark, NJ for US East) |
| Plan | **Dedicated 4GB** ($36/mo) — 2 CPU, 4GB RAM, 80GB SSD |
| Label | `eventflow-prod` |
| Root Password | Strong, unique password (you'll disable root later) |
| SSH Key | Add your public key |
| Backups | Enable ($2/mo — recommended) |
| Private IP | Enable (for future database separation) |

4. Click **Create Linode** — provisioning takes ~60 seconds
5. Note the **public IP address**

### Via Linode CLI (Alternative)

```bash
# Install Linode CLI
pip install linode-cli

# Create the instance
linode-cli linodes create \
  --type g6-dedicated-2 \
  --region us-east \
  --image linode/ubuntu24.04 \
  --label eventflow-prod \
  --root_pass "YOUR_STRONG_PASSWORD" \
  --authorized_keys "$(cat ~/.ssh/id_ed25519.pub)" \
  --backups_enabled true \
  --private_ip true
```

---

## 3. DNS Configuration

Point your domain to the Linode IP. In your DNS provider:

| Record | Name | Value | TTL |
|--------|------|-------|-----|
| A | eventflow (or @) | YOUR_LINODE_IP | 300 |
| AAAA | eventflow (or @) | YOUR_LINODE_IPV6 | 300 |

Or use **Linode DNS Manager** (free):

1. Cloud Manager → Domains → Create Domain
2. Add A record pointing to your Linode IP
3. Update your registrar's nameservers to Linode's:
   - `ns1.linode.com`
   - `ns2.linode.com`
   - `ns3.linode.com`
   - `ns4.linode.com`
   - `ns5.linode.com`

Wait for DNS propagation (check with `dig eventflow.yourdomain.com`).

---

## 4. SSH Key Setup

Generate a **dedicated deploy key** (separate from your personal key):

```bash
# On your LOCAL machine
ssh-keygen -t ed25519 -C "eventflow-deploy" -f ~/.ssh/eventflow_deploy

# Copy to server
ssh-copy-id -i ~/.ssh/eventflow_deploy.pub root@YOUR_LINODE_IP

# Test connection
ssh -i ~/.ssh/eventflow_deploy root@YOUR_LINODE_IP "echo 'Connected!'"
```

Save the **private key** contents — you'll need it for GitHub Secrets:

```bash
cat ~/.ssh/eventflow_deploy
# Copy the ENTIRE output including BEGIN and END lines
```

---

## 5. Server Setup (Automated)

The setup script handles everything: security hardening, Docker, Nginx, SSL, backups.

```bash
# Copy the setup script to your server
scp -i ~/.ssh/eventflow_deploy scripts/linode-setup.sh root@YOUR_LINODE_IP:/root/

# SSH in and run it
ssh -i ~/.ssh/eventflow_deploy root@YOUR_LINODE_IP

# On the server:
chmod +x /root/linode-setup.sh
bash /root/linode-setup.sh
```

The script will prompt for:
- Your domain name
- Email for SSL certificates
- GitHub repository URL

### What the script does:

1. **System hardening** — firewall (UFW), fail2ban, SSH lockdown, auto-updates
2. **Docker installation** — Docker Engine + Compose plugin with log rotation
3. **Nginx** — installed as host-level reverse proxy
4. **SSL** — Let's Encrypt certificate with auto-renewal
5. **Application** — clones repo to `/opt/eventflow`, creates `.env`
6. **Backups** — daily cron job for PostgreSQL dumps
7. **Kernel tuning** — TCP/connection optimizations for production

---

## 6. GitHub Repository Setup

### Initialize the repo locally:

```bash
cd eventflow-pro

# Initialize git
git init
git add .
git commit -m "Initial commit: full EventFlow Pro stack"

# Add remote and push
git remote add origin https://github.com/saikiclawd/evently.git
git branch -M main
git push -u origin main
```

### Branch protection (recommended):

1. GitHub → Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - Require pull request reviews
   - Require status checks (test-backend, test-frontend)
   - Require branches to be up to date

---

## 7. GitHub Secrets Configuration

Go to **GitHub → Repository → Settings → Secrets and variables → Actions**

Add these **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `LINODE_HOST` | `YOUR_LINODE_IP` | Public IP of your Linode |
| `DEPLOY_USER` | `deploy` | SSH username |
| `SSH_PRIVATE_KEY` | Contents of `~/.ssh/eventflow_deploy` | Full private key with BEGIN/END |
| `SSH_PORT` | `22` | SSH port |

Add an **Environment** called `production`:

1. Settings → Environments → New environment → `production`
2. Add protection rules if desired (required reviewers, wait timer)

---

## 8. First Deployment

### Configure environment variables:

```bash
ssh -i ~/.ssh/eventflow_deploy deploy@YOUR_LINODE_IP

# Edit the environment file
cd /opt/eventflow
nano .env
```

Fill in ALL required values (Stripe keys, SendGrid, database passwords, etc.).

### Start the stack:

```bash
cd /opt/eventflow

# Build and start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Watch the logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Run initial database migration
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api flask db upgrade

# Verify health
curl http://localhost:5000/api/v1/health
curl http://localhost:3000/
```

### Verify SSL:

Open `https://eventflow.yourdomain.com` in your browser. You should see the React app with a valid SSL certificate.

---

## 9. Ongoing Deployments (CI/CD)

Once GitHub Secrets are configured, every push to `main` triggers automatic deployment:

```
Push to main
    ↓
GitHub Actions triggered
    ↓
┌─────────────────────────┐
│ Job 1: Test Backend     │ ← pytest + linting
│ Job 2: Test Frontend    │ ← build + lint
└─────────┬───────────────┘
          ↓ (both pass)
┌─────────────────────────┐
│ Job 3: Build Images     │ ← Docker build + push to GHCR
└─────────┬───────────────┘
          ↓
┌─────────────────────────┐
│ Job 4: Deploy to Linode │ ← SSH + rolling restart
└─────────────────────────┘
```

### Rolling deployment (zero downtime):

The deploy job restarts API instances sequentially:
1. Restart `api` → wait 10s → health check
2. Restart `api-2` → wait 5s
3. Restart remaining services

Nginx load-balances between both API instances, so at least one is always running.

### Manual deployment:

```bash
ssh deploy@YOUR_LINODE_IP
cd /opt/eventflow
bash scripts/deploy.sh
```

---

## 10. Monitoring & Maintenance

### Check service status:

```bash
# All containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Logs (follow)
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f api

# Specific service logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f celery-worker
```

### Database operations:

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U eventflow -d eventflow_pro

# Manual backup
bash /opt/eventflow/scripts/backup.sh

# Restore from backup
gunzip < /opt/eventflow/backups/eventflow_20260319.sql.gz | \
    docker compose exec -T postgres psql -U eventflow -d eventflow_pro
```

### Resource monitoring:

```bash
# System resources
htop

# Docker resource usage
docker stats

# Disk usage
df -h
ncdu /opt/eventflow
```

### SSL certificate renewal:

Automatic via cron. To manually renew:

```bash
sudo certbot renew --dry-run   # Test first
sudo certbot renew
sudo systemctl reload nginx
```

---

## 11. Troubleshooting

### Container won't start:

```bash
# Check logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs api

# Check if port is in use
sudo lsof -i :5000

# Rebuild from scratch
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Database connection refused:

```bash
# Check if postgres container is healthy
docker compose exec postgres pg_isready -U eventflow

# Check DATABASE_URL in .env matches docker-compose service name
# Should be: postgresql://eventflow:PASSWORD@postgres:5432/eventflow_pro
```

### Nginx 502 Bad Gateway:

```bash
# Check if API container is running
docker compose ps api
curl http://localhost:5000/api/v1/health

# Check nginx config
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### GitHub Actions deploy fails:

- Verify SSH key in GitHub Secrets matches the key on the server
- Check the deploy user has docker permissions: `groups deploy`
- Verify the server can reach GitHub: `ssh deploy@SERVER "git ls-remote origin"`

### Out of disk space:

```bash
# Clean Docker system
docker system prune -a --volumes

# Check largest directories
sudo ncdu /

# Clean old backups
find /opt/eventflow/backups -mtime +7 -delete
```

---

## 12. Cost Breakdown

### Monthly Infrastructure Cost:

| Resource | Service | Cost |
|----------|---------|------|
| Compute | Linode Dedicated 4GB (2 CPU, 4GB RAM) | $36/mo |
| Backups | Linode Backup Service | $2/mo |
| Storage | Linode Object Storage (250GB) | $5/mo |
| DNS | Linode DNS Manager | Free |
| SSL | Let's Encrypt | Free |
| CI/CD | GitHub Actions (2,000 min free) | Free |
| Container Registry | GitHub Container Registry (500MB free) | Free |
| DDoS Protection | Included with Linode | Free |
| **Total** | | **~$43/mo** |

### Scaling path:

| Growth Stage | Plan | Cost | Capacity |
|-------------|------|------|----------|
| Launch | Dedicated 4GB | $36/mo | ~50 concurrent users |
| Growth | Dedicated 8GB | $72/mo | ~200 concurrent users |
| Scale | Dedicated 16GB + Managed DB | $200/mo | ~500+ concurrent users |
| Enterprise | LKE Kubernetes cluster | $300+/mo | Unlimited horizontal scale |

### When to upgrade:

- CPU consistently above 70% → upgrade plan
- RAM above 85% → upgrade plan
- Need HA database → add Linode Managed PostgreSQL ($15/mo+)
- Multiple regions → migrate to LKE (Kubernetes)

---

## Architecture Summary

```
Internet
    │
    ▼
┌─────────────┐
│   Linode    │
│   Firewall  │ (UFW: 22, 80, 443 only)
└──────┬──────┘
       │
┌──────▼──────┐
│    Nginx    │ SSL termination + reverse proxy
│  (Host)     │ Rate limiting + security headers
└──┬───┬───┬──┘
   │   │   │
   │   │   └──────────────────────┐
   │   │                          │
┌──▼───┴──┐  ┌──────────┐  ┌─────▼─────┐
│ React   │  │ Flask    │  │ Flask     │
│ Frontend│  │ API #1   │  │ API #2    │
│ :3000   │  │ :5000    │  │ :5001     │
└─────────┘  └──┬───┬───┘  └──┬────┬──┘
                │   │          │    │
        ┌───────┘   └──────────┘    │
        │                           │
   ┌────▼─────┐  ┌────────────┐   │
   │PostgreSQL│  │   Redis    │◄──┘
   │  :5432   │  │   :6379    │
   └──────────┘  └──────┬─────┘
                        │
              ┌─────────▼──────────┐
              │  Celery Workers    │
              │  + Celery Beat     │
              └────────────────────┘
```

# Evently — Full-Stack Event Rental SaaS

> React.js Frontend + Flask Backend · Deployed on Akamai Linode

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Akamai Linode VPS                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  Nginx   │→ │  React   │  │  Flask   │  │ Celery │  │
│  │  Reverse │→ │  (static)│  │  API x2  │  │Workers │  │
│  │  Proxy   │→ │  :3000   │  │  :5000   │  │        │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │PostgreSQL│  │  Redis   │  │  Celery  │              │
│  │  :5432   │  │  :6379   │  │  Beat    │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Quick Start — Local Development

```bash
# 1. Clone
git clone https://github.com/saikiclawd/evently.git
cd evently

# 2. Copy environment file
cp .env.example .env   # edit with your keys

# 3. Start everything
docker compose up --build

# 4. Access
# Frontend:  http://localhost:3000
# API:       http://localhost:5000/api/v1/health
# Flower:    http://localhost:5555 (Celery monitor)
```

## Deploy to Akamai Linode

See **`DEPLOYMENT.md`** for the complete step-by-step guide.

### TL;DR
```bash
# 1. Provision Linode (Dedicated 4GB+ recommended)
# 2. Run the setup script on your Linode
scp scripts/linode-setup.sh root@YOUR_LINODE_IP:/root/
ssh root@YOUR_LINODE_IP "bash /root/linode-setup.sh"

# 3. Push to GitHub → CI/CD auto-deploys
git push origin main
```

## Project Structure

```
evently/
├── .github/workflows/
│   └── deploy.yml              # CI/CD pipeline
├── backend/
│   ├── app/
│   │   ├── __init__.py         # Flask app factory
│   │   ├── config.py           # Settings
│   │   ├── extensions.py       # SQLAlchemy, Redis, etc.
│   │   ├── models/             # Database models
│   │   ├── api/v1/             # REST endpoints
│   │   ├── services/           # Business logic
│   │   └── tasks/              # Celery tasks
│   ├── migrations/             # Alembic migrations
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── gunicorn.conf.py
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf              # Frontend container nginx
├── nginx/
│   └── evently.conf          # Main reverse proxy config
├── docker/
│   ├── docker-compose.yml      # Local development
│   └── docker-compose.prod.yml # Production overrides
├── scripts/
│   ├── linode-setup.sh         # Server provisioning
│   ├── deploy.sh               # Deployment script
│   ├── backup.sh               # Database backup
│   └── ssl-setup.sh            # Let's Encrypt SSL
├── .env.example
├── DEPLOYMENT.md
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Zustand, React Query, TailwindCSS |
| Backend | Flask 3.x, SQLAlchemy 2.x, Alembic, Marshmallow |
| Database | PostgreSQL 16, Redis 7 |
| Task Queue | Celery 5.x + Celery Beat |
| Web Server | Nginx 1.25, Gunicorn (gevent) |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Hosting | Akamai Linode (Dedicated 4GB+) |
| SSL | Let's Encrypt (Certbot) |
| Payments | Stripe Connect |
| Email | SendGrid |
| Storage | Linode Object Storage (S3-compatible) |

## License

Proprietary — All rights reserved.

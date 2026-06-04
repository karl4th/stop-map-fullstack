# StopMap

A stop-card management system for industrial safety at KazAtomProm subsidiaries.
Workers submit stop cards via Telegram bot; managers and admins review them through a web panel.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + SQLAlchemy (async) + Alembic |
| Database | PostgreSQL 16 |
| Cache / Bot state | Redis 7 |
| File storage | MinIO |
| Telegram bot | aiogram 3 |
| Admin panel | Next.js 16 |
| Runtime | Python 3.13 / Node 20 |
| Infra | Docker Compose |

## Architecture

```
Browser ──────► Nginx :80 ──► Frontend :3000
                           └──► Backend :8000 ──► PostgreSQL
                                              ├──► Redis
Telegram ──► Bot ──────────► Backend          └──► MinIO
```

### User roles

| Role | Access |
|------|--------|
| `worker` | Telegram bot only — submit stop cards |
| `manager` | Web panel — approve workers in their section, review stop cards |
| `admin` | Web panel — full access: manage sections, users, all stop cards |

### Stop card lifecycle

```
issued → acknowledged → closed
                     → disputed
```

## Development

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ with [uv](https://github.com/astral-sh/uv)
- Node.js 20+

### Setup

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your values

# 2. Start infrastructure
cd docker
docker compose --env-file ../.env up -d

# 3. Run migrations
cd ../backend
uv sync
uv run alembic upgrade head

# 4. Start backend
uv run uvicorn app.main:app --reload

# 5. Start frontend
cd ../frontend
npm install
npm run dev

# 6. Start bot
cd ../telegram
uv sync
uv run python -m app.main
```

Backend API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs  
Frontend: http://localhost:3000  
MinIO console: http://localhost:9001

First admin credentials are set via `.env` (`FIRST_ADMIN_PHONE` / `FIRST_ADMIN_PASSWORD`).

## Production deployment

### 1. Prepare environment

```bash
cp .env.example .env
```

Fill in all values. Generate secrets:

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Strong passwords
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Set `CORS_ORIGINS` to your actual domain (e.g. `https://stopmap.yourdomain.com`).  
Set `MINIO_PUBLIC_ENDPOINT` to the publicly accessible MinIO host.

### 2. Build and start

```bash
cd docker
docker compose -f docker-compose.prod.yml --env-file ../.env up -d --build
```

This starts all services behind Nginx on port 80. No database ports are exposed externally.

### 3. Run migrations

```bash
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head
```

### 4. HTTPS (recommended)

Place a TLS-terminating reverse proxy (Caddy, Nginx with Certbot, Cloudflare Tunnel) in front of port 80.

## Environment variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_*` | PostgreSQL connection settings |
| `REDIS_URL` | Redis connection URL |
| `MINIO_ENDPOINT` | MinIO internal endpoint (used by backend for uploads) |
| `MINIO_PUBLIC_ENDPOINT` | MinIO public endpoint (must be reachable by browsers) |
| `MINIO_ACCESS_KEY` | MinIO access key |
| `MINIO_SECRET_KEY` | MinIO secret key |
| `MINIO_BUCKET` | Bucket name for photo storage |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `FIRST_ADMIN_PHONE` | Phone number of the bootstrap admin account |
| `FIRST_ADMIN_NAME` | Display name of the bootstrap admin |
| `FIRST_ADMIN_PASSWORD` | Password for the bootstrap admin |
| `APP_ENV` | `development` or `production` |
| `SECRET_KEY` | JWT signing secret (min 32 bytes of entropy) |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins |

## API

All endpoints are under `/api`:

| Prefix | Auth | Description |
|--------|------|-------------|
| `/api/admin/*` | JWT (admin) | Admin panel endpoints |
| `/api/manager/*` | JWT (manager/admin) | Manager panel endpoints |
| `/api/bot/*` | `X-Bot-Token` header | Telegram bot endpoints |
| `/api/photos/{key}` | JWT | Photo proxy (streams from MinIO) |

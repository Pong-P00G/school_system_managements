# 🎓 School Management System

A comprehensive university management system built with **FastAPI** (backend), **Vue 3** (frontend), **Tailwind CSS v4** (styling), and **PostgreSQL 18** (database).

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Deployment](#deployment)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Vue 3 +    │────▶│  FastAPI     │────▶│ PostgreSQL   │
│  Tailwind 4 │     │  Backend     │     │ 18           │
│  :5173      │     │  :8000       │     │ :5432        │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐     ┌──────────────┐
                    │  Prometheus  │────▶│  Grafana     │
                    │  :9090       │     │  :3000       │
                    └──────────────┘     └──────────────┘
```

### Project Structure

```
School Management System/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints (health, auth, users, departments, courses)
│   │   ├── core/              # Config, database, security
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend unit tests (pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Vue 3 frontend
│   ├── src/
│   │   ├── pages/             # Dashboard, Departments, Courses, Users
│   │   ├── components/        # Reusable components + tests
│   │   ├── api.js             # Axios API client
│   │   ├── router.js          # Vue Router config
│   │   └── style.css          # Tailwind CSS v4
│   ├── Dockerfile
│   └── package.json
├── monitoring/                 # Prometheus + Grafana configs
├── scripts/                    # Deploy, backup, restore scripts
├── tests/                      # E2E (Cypress), performance (JMeter), security (ZAP)
├── .github/workflows/          # CI/CD pipeline
├── docker-compose.yml          # Full stack orchestration
└── school_system_db_v2.sql     # Database schema
```

## ✅ Prerequisites

- **Docker** >= 24.0 and **Docker Compose** >= 2.20
- **Node.js** >= 22 (for local frontend development)
- **Python** >= 3.12 (for local backend development)

## 🚀 Quick Start

The fastest way to run the entire stack:

```bash
# Clone and start all services
docker compose up -d

# Wait ~30 seconds for all services to initialize, then visit:
# Frontend:   http://localhost:5173
# Backend:    http://localhost:8000
# API Docs:   http://localhost:8000/docs
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
```

The PostgreSQL database is automatically initialized with the schema from `school_system_db_v2.sql`.

## 🛠️ Development Setup

### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vue 3 + Tailwind CSS v4)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Database (PostgreSQL)

```bash
# Start only the database service
docker compose up -d db

# Load schema manually (if needed)
docker exec -i school_db psql -U school_admin school_system_db < school_system_db_v2.sql
```

## 📡 API Documentation

Once the backend is running, interactive API docs are available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/health/db` | Database health check |
| POST | `/api/v1/auth/login` | User login (JWT) |
| POST | `/api/v1/auth/register` | User registration |
| GET | `/api/v1/users/` | List users |
| GET | `/api/v1/departments/` | List departments |
| POST | `/api/v1/departments/` | Create department |
| GET | `/api/v1/courses/` | List courses |
| POST | `/api/v1/courses/` | Create course |

## 🧪 Testing

### Backend Unit Tests (pytest)

```bash
cd backend
pytest tests/ -v
```

### Frontend Integration Tests (Vue Test Utils)

```bash
cd frontend
npm install --save-dev @vue/test-utils vitest jsdom
npx vitest run
```

### End-to-End Tests (Cypress)

```bash
# Install Cypress globally or locally
npm install -g cypress

# Run E2E tests (with app running)
cypress run --config-file tests/e2e/cypress.config.js
```

### Performance Tests (JMeter)

```bash
# Run JMeter test plan (requires JMeter installed)
jmeter -n -t tests/jmeter/api-performance-test.jmx -l results/jmeter-results.jtl
```

### Security Tests (OWASP ZAP)

```bash
# Run ZAP API scan using Docker
docker run -v $(pwd)/tests/security:/zap/wrk/:rw \
  ghcr.io/zaproxy/zaproxy:stable zap-api-scan.py \
  -t http://host.docker.internal:8000/openapi.json \
  -f openapi \
  -c zap-config.yml
```

## 📊 Monitoring

### Prometheus

- URL: http://localhost:9090
- Scrapes metrics from the FastAPI backend at `/metrics`
- Configuration: `monitoring/prometheus.yml`

### Grafana

- URL: http://localhost:3000
- Default credentials: `admin` / `admin`
- Prometheus datasource is auto-provisioned
- Create dashboards for API response times, error rates, etc.

## 🚢 Deployment

### Using the Deploy Script

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Manual Deployment

```bash
# 1. Pull latest code
git pull origin main

# 2. Build and start services
docker compose build --no-cache
docker compose up -d

# 3. Verify
curl http://localhost:8000/api/v1/health
```

### Production Considerations

1. **Change secrets**: Update `SECRET_KEY` in environment variables
2. **Use proper PostgreSQL image**: Replace `postgres:18-beta1` with stable release when available
3. **Enable HTTPS**: Add nginx reverse proxy with SSL certificates
4. **Set `DEBUG=false`**: Disable debug mode in production
5. **Configure proper CORS origins**: Restrict to your domain
6. **Set up log aggregation**: Forward logs to ELK stack or similar
7. **Configure resource limits**: Set Docker memory/CPU limits

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:

1. Runs backend pytest tests
2. Builds frontend
3. Builds Docker images
4. Deploys to production (on main branch push)

## 💾 Backup & Recovery

### Create Backup

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

Backups are saved to `./backups/` as compressed SQL dumps with timestamps.

### Restore from Backup

```bash
chmod +x scripts/restore.sh
./scripts/restore.sh ./backups/school_system_db_20240101_120000.sql.gz
```

### Automated Backups

Add to crontab for daily backups:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/project/scripts/backup.sh >> /var/log/school-backup.log 2>&1
```

## 🔧 Troubleshooting

### Common Issues

#### Docker containers won't start

```bash
# Check container logs
docker compose logs -f

# Check specific service
docker compose logs backend
docker compose logs db
```

#### Database connection refused

```bash
# Verify database is running
docker compose ps db

# Check database health
docker exec school_db pg_isready -U school_admin

# Restart database
docker compose restart db
```

#### Frontend can't reach backend

1. Verify backend is running: `curl http://localhost:8000/api/v1/health`
2. Check CORS settings in `backend/.env`
3. Verify Vite proxy config in `frontend/vite.config.js`

#### Port conflicts

```bash
# Check what's using a port (Windows)
netstat -ano | findstr :8000
netstat -ano | findstr :5173
netstat -ano | findstr :5432

# Change ports in docker-compose.yml if needed
```

#### Database schema issues

```bash
# Re-initialize database
docker compose down -v  # WARNING: deletes all data
docker compose up -d db
docker exec -i school_db psql -U school_admin school_system_db < school_system_db_v2.sql
```

#### Backend dependency issues

```bash
cd backend
pip install --upgrade -r requirements.txt
```

#### Frontend build errors

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📄 License

This project is for educational purposes.

# OpsPilot - DevOps Automation Platform

A comprehensive DevOps automation platform for managing servers, monitoring, and remote execution.

## Project Structure

```
/Volumes/ashrul/Development/Active/opspilot/
├── frontend/              # Vue 3 + TypeScript frontend (Geeker Admin)
├── backend/               # FastAPI backend
├── infrastructure/        # Terraform + Helm (IaC)
├── salt/                  # SaltStack states
├── docker-compose.yml     # Local development services
└── .env.example           # Environment variables template
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for frontend)
- Python 3.11+ (for backend)
- Git

### 1. Start Local Services

```bash
cd /Volumes/ashrul/Development/Active/opspilot
docker-compose up -d
```

This starts:
- PostgreSQL 15 with TimescaleDB (port 5432)
- Redis 7 (port 6379)
- HashiCorp Vault (port 8200)
- pgAdmin (port 5050) - PostgreSQL GUI
- Redis Insight (port 8001) - Redis GUI

### 2. Frontend Setup

```bash
cd /Volumes/ashrul/Development/Active/opspilot/frontend
pnpm install
pnpm dev
```

Frontend will be available at http://localhost:5173

### 3. Backend Setup

```bash
cd /Volumes/ashrul/Development/Active/opspilot/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
# Edit .env with your values

# Run migrations (when implemented)
# alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Salt Master (Optional)

```bash
cd /Volumes/ashrul/Development/Active/opspilot/salt
# Follow instructions in README.md
```

## Services

| Service | Port | Access |
|---------|------|--------|
| Frontend | 8848 | http://localhost:8848 |
| Backend API | 8000 | http://localhost:8000 |
| PostgreSQL | 5438 | localhost:5438 |
| Redis | 6384 | localhost:6384 |
| Vault | 8201 | http://localhost:8201 |
| pgAdmin | 5051 | http://localhost:5051 |
| Redis Insight | 8002 | http://localhost:8002 |

## Documentation

- **Index**: [docs/README.md](docs/README.md) — deployment, troubleshooting, archive, and status
- **Project status**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **PRD**: May live outside this repository (for example a sibling `prds/` tree); not bundled here
- **Backend**: See `backend/README.md`
- **Infrastructure**: See `infrastructure/README.md`
- **Salt**: See `salt/README.md`

## Development Workflow

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
pnpm test
```

### Code Quality

```bash
# Backend - Format and lint
cd backend
black .
ruff check .
mypy app/

# Frontend - Format and lint
cd frontend
pnpm lint
pnpm format
```

### Building Docker Images

```bash
# Backend
cd backend
docker build -t opspilot-backend:latest -f ../infrastructure/docker/Dockerfile.backend .

# Frontend
cd frontend
docker build -t opspilot-frontend:latest -f ../infrastructure/docker/Dockerfile.frontend .
```

## Stopping Services

```bash
docker-compose down
```

To also remove volumes:
```bash
docker-compose down -v
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker logs opspilot-postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Vault Unsealed

In dev mode, Vault is automatically unsealed with token `dev-root-token`.

### Redis Connection Issues

```bash
# Check Redis logs
docker logs opspilot-redis

# Test Redis connection
redis-cli ping
```

## Next Steps

1. Implement authentication (JWT, OAuth)
2. Set up database migrations with Alembic
3. Implement SaltStack integration
4. Set up CI/CD pipeline
5. Configure production infrastructure

## License

MIT

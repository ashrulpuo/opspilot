# OpsPilot Backend

FastAPI-based backend for the OpsPilot DevOps Automation Platform.

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Python**: 3.11+
- **Database**: PostgreSQL 15+ with TimescaleDB 2.11+
- **Cache**: Redis 7+
- **Secrets**: HashiCorp Vault
- **Task Queue**: Celery
- **Remote Execution**: SaltStack

## Project Structure

```
opspilot-backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Configuration, security, dependencies
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── repositories/     # Data access layer
│   ├── agents/           # SaltStack integration
│   └── utils/            # Utilities
├── alembic/              # Database migrations
├── tests/                # Test suite
├── pyproject.toml        # Project dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with TimescaleDB extension
- Redis 7+
- HashiCorp Vault

### Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `VAULT_ADDR`: Vault server address
- `VAULT_TOKEN`: Vault authentication token
- `SECRET_KEY`: JWT secret key

### Database Setup

```bash
# Run migrations
alembic upgrade head

# (Optional) Seed database
python -m app.scripts.seed
```

### Running

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Running Celery Worker

```bash
celery -A app.celery worker --loglevel=info
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Security Notes

- All secrets managed via HashiCorp Vault
- Passwords hashed using bcrypt
- JWT tokens for authentication
- Rate limiting on API endpoints
- Input validation via Pydantic schemas

## License

MIT

"""
Pytest configuration for backend tests.
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db


# Test database URL (SQLite in-memory for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        future=True,
        echo=False
    )
    return engine


@pytest.fixture(scope="session")
async def init_db(test_engine):
    """Initialize test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_engine, init_db):
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """Create test HTTP client with database override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_metrics():
    """Sample metrics data."""
    return [
        {
            "metric_name": "cpu_total_user",
            "metric_value": 25.5,
            "unit": "percent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "metric_name": "cpu_total_system",
            "metric_value": 5.0,
            "unit": "percent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "metric_name": "cpu_total_idle",
            "metric_value": 69.5,
            "unit": "percent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]


@pytest.fixture
def sample_beacon_data():
    """Sample beacon data."""
    return {
        "beacon_type": "disk_usage",
        "event_data": {
            "mountpoint": "/",
            "used_percent": 85.5,
            "used_gb": 42.75,
            "total_gb": 50.0,
            "fstype": "ext4"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_service_data():
    """Sample service data."""
    return {
        "services": [
            {
                "name": "nginx",
                "status": "running",
                "pid": 1234
            },
            {
                "name": "postgresql",
                "status": "stopped",
                "pid": None
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_process_data():
    """Sample process data."""
    return {
        "processes": [
            {
                "pid": 1234,
                "name": "nginx",
                "command": "nginx: master process",
                "username": "www-data",
                "cpu_percent": 2.5,
                "memory_percent": 1.2,
                "state": "S",
                "start_time": datetime.now(timezone.utc).isoformat()
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_package_data():
    """Sample package data."""
    return {
        "packages": [
            {
                "name": "nginx",
                "version": "1.24.0-2",
                "architecture": "amd64",
                "source": "dpkg",
                "is_update_available": True,
                "installed_date": datetime.now(timezone.utc).isoformat(),
                "update_version": "1.25.0-1"
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_log_data():
    """Sample log data."""
    return {
        "logs": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "log_level": "INFO",
                "source": "nginx",
                "message": "Configuration reloaded successfully"
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "log_level": "ERROR",
                "source": "postgresql",
                "message": "Connection failed: connection refused"
            }
        ]
    }

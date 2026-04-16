"""Database connection and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database (create all tables)."""
    # This is primarily for development/testing
    # In production, use Alembic migrations
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models import user, organization, server, alert, ssh_session

        # Create extensions (TimescaleDB)
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

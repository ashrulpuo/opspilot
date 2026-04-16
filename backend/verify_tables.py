"""Verify database tables."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5438/opspilot"

async def verify_tables():
    """Verify all tables were created."""
    engine = create_async_engine(DATABASE_URL)

    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))

        tables = [row[0] for row in result.fetchall()]
        print("Created tables:")
        for table in tables:
            print(f"  - {table}")

        # Check if metrics is a hypertable
        result = await conn.execute(text("""
            SELECT hypertable_name
            FROM timescaledb_information.hypertables
            WHERE hypertable_schema = 'public';
        """))

        hypertables = [row[0] for row in result.fetchall()]
        print("\nHypertables:")
        for hypertable in hypertables:
            print(f"  - {hypertable}")

        # Check retention policies
        result = await conn.execute(text("""
            SELECT hypertable_name, retention_period
            FROM timescaledb_information.jobs
            WHERE hypertable_schema = 'public'
            AND proc_name = 'policy_retention';
        """))

        policies = result.fetchall()
        if policies:
            print("\nRetention policies:")
            for hypertable, period in policies:
                print(f"  - {hypertable}: {period}")
        else:
            print("\nNo retention policies found (using default timescaledb retention)")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_tables())

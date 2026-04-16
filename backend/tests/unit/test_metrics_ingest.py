"""Metrics ingest with per-server API key (async DB + ASGI)."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.agent_keys import generate_agent_api_key, hash_agent_api_key
from app.core.database import Base, get_db
from app.main import app
from app.models.organization import Organization, OrganizationMember
from app.models.server import Server
from app.models.user import User


@pytest_asyncio.fixture
async def ingest_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    uid = str(uuid.uuid4())
    oid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    plain_key = generate_agent_api_key()
    now = datetime.utcnow()

    async with session_factory() as s:
        s.add(
            User(
                id=uid,
                email="metrics-ingest@test.local",
                password_hash="x",
                full_name="Test",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        s.add(
            Organization(
                id=oid,
                name="Org",
                slug="metrics-ingest-org",
                created_at=now,
                updated_at=now,
            )
        )
        s.add(OrganizationMember(user_id=uid, organization_id=oid, role="admin"))
        s.add(
            Server(
                id=sid,
                organization_id=oid,
                hostname="h1",
                ip_address="127.0.0.1",
                os_type="linux",
                status="online",
                agent_api_key_hash=hash_agent_api_key(plain_key),
                created_at=now,
                updated_at=now,
            )
        )
        await s.commit()

    transport = ASGITransport(app=app)
    ac = AsyncClient(transport=transport, base_url="http://test")
    try:
        yield ac, sid, oid, plain_key
    finally:
        await ac.aclose()
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ingest_metrics_success(ingest_client):
    client, sid, oid, key = ingest_client
    r = await client.post(
        f"/api/v1/servers/{sid}/metrics",
        headers={"X-API-Key": key},
        json={
            "server_id": sid,
            "organization_id": oid,
            "metrics": {"cpu": 1.0},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["server_id"] == sid


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ingest_metrics_rejects_wrong_key(ingest_client):
    client, sid, oid, _key = ingest_client
    r = await client.post(
        f"/api/v1/servers/{sid}/metrics",
        headers={"X-API-Key": "wrong-key"},
        json={
            "server_id": sid,
            "organization_id": oid,
            "metrics": {"cpu": 1.0},
        },
    )
    assert r.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ingest_metrics_rejects_org_mismatch(ingest_client):
    client, sid, _oid, key = ingest_client
    r = await client.post(
        f"/api/v1/servers/{sid}/metrics",
        headers={"X-API-Key": key},
        json={
            "server_id": sid,
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "metrics": {"cpu": 1.0},
        },
    )
    assert r.status_code == 400

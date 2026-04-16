"""Tests for fresh-install bootstrap (first admin) endpoints.

Vertical trace: HTTP POST /api/v1/auth/bootstrap -> auth.bootstrap_first_admin ->
get_password_hash / User + Organization + OrganizationMember ORM -> commit ->
create_access_token -> LoginResponse.
"""
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db
from app.models.installation_state import InstallationState  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401


@pytest_asyncio.fixture
async def bootstrap_client(monkeypatch: pytest.MonkeyPatch):
    """In-memory SQLite app with dependency override for get_db."""
    # Avoid flaky 429 when a real Redis on localhost still holds bootstrap_rate:* keys.
    monkeypatch.setattr(
        "app.api.v1.auth.check_rate_limit",
        AsyncMock(return_value=True),
    )
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_setup_required_true_when_empty(bootstrap_client: AsyncClient):
    response = await bootstrap_client.get("/api/v1/auth/setup-required")
    assert response.status_code == 200
    assert response.json() == {"setup_required": True}


@pytest.mark.asyncio
async def test_bootstrap_returns_token_and_second_bootstrap_forbidden(bootstrap_client: AsyncClient):
    response = await bootstrap_client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "admin@example.com",
            "password": "SecurePass1!",
            "confirm_password": "SecurePass1!",
            "full_name": "Admin User",
            "organization_name": "Acme Ops",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@example.com"

    status = await bootstrap_client.get("/api/v1/auth/setup-required")
    assert status.json() == {"setup_required": False}

    again = await bootstrap_client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "other@example.com",
            "password": "SecurePass1!",
            "confirm_password": "SecurePass1!",
            "full_name": "Other",
        },
    )
    assert again.status_code == 403


@pytest.mark.asyncio
async def test_list_organizations_after_bootstrap(bootstrap_client: AsyncClient):
    boot = await bootstrap_client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "orgapi@example.com",
            "password": "SecurePass1!",
            "confirm_password": "SecurePass1!",
            "full_name": "Org Api User",
            "organization_name": "Listed Org",
        },
    )
    assert boot.status_code == 200
    token = boot.json()["access_token"]
    resp = await bootstrap_client.get(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["name"] == "Listed Org"


@pytest.mark.asyncio
async def test_register_forbidden_when_public_reg_disabled_even_with_users(bootstrap_client: AsyncClient):
    await bootstrap_client.post(
        "/api/v1/auth/bootstrap",
        json={
            "email": "first@example.com",
            "password": "SecurePass1!",
            "confirm_password": "SecurePass1!",
            "full_name": "First",
        },
    )
    reg = await bootstrap_client.post(
        "/api/v1/auth/register",
        json={
            "email": "second@example.com",
            "password": "SecurePass1!",
            "confirm_password": "SecurePass1!",
            "full_name": "Second",
        },
    )
    assert reg.status_code == 403


@pytest.mark.asyncio
async def test_register_forbidden_on_empty_db_when_public_reg_disabled(bootstrap_client: AsyncClient):
    reg = await bootstrap_client.post(
        "/api/v1/auth/register",
        json={
            "email": "solo@example.com",
            "password": "SecurePass1!",
            "confirm_password": "SecurePass1!",
            "full_name": "Solo",
        },
    )
    assert reg.status_code == 403

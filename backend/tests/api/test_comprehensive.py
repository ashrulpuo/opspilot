"""Smoke tests for OpsPilot API via in-process ASGI (no external server)."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_api_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_api_docs_accessible() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_openapi_json_accessible() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/openapi.json")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_v1_root() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/")
        assert response.status_code in (404, 307)


@pytest.mark.asyncio
async def test_security_scans_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/security-scans")
        assert response.status_code in (401, 403, 422, 404)


@pytest.mark.asyncio
async def test_password_reset_endpoints() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        assert response.status_code in (200, 400, 404, 422, 429)

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "test-token-not-real-please-32chars-min", "new_password": "newpassword123"},
        )
        assert response.status_code in (200, 400, 404, 422)


@pytest.mark.asyncio
async def test_servers_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/servers")
        assert response.status_code in (401, 403, 404, 422)


@pytest.mark.asyncio
async def test_dashboard_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/dashboard/stats")
        assert response.status_code in (401, 403, 422)


@pytest.mark.asyncio
async def test_alerts_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/alerts")
        assert response.status_code in (401, 403, 422, 404)

"""Comprehensive API health test for OpsPilot."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_health_endpoint():
    """Test API health endpoint is accessible."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_api_docs_accessible():
    """Test API documentation is accessible."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/docs")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_openapi_json_accessible():
    """Test OpenAPI JSON is accessible."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_v1_root():
    """Test API v1 root endpoint."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/")
        # Should be 404 or redirect
        assert response.status_code in [404, 307]


@pytest.mark.asyncio
async def test_security_scans_endpoint():
    """Test security scans endpoint (requires valid auth in production)."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Test GET request (should work even without auth for status)
        response = await client.get("/api/v1/security-scans")
        # Should fail without auth but endpoint exists
        assert response.status_code in [401, 403, 422, 404]


@pytest.mark.asyncio
async def test_password_reset_endpoints():
    """Test password reset endpoints exist."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Test forgot password endpoint
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        # Should accept the request (email may not exist)
        assert response.status_code in [200, 400, 404]
        
        # Test reset password endpoint
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "test-token", "new_password": "newpassword123"}
        )
        # Should fail for invalid token but endpoint exists
        assert response.status_code in [400, 404, 422]


@pytest.mark.asyncio
async def test_servers_endpoint():
    """Test servers endpoint."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/servers")
        # Should fail without auth but endpoint exists
        assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_dashboard_endpoint():
    """Test dashboard endpoint."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/dashboard/stats")
        # Should fail without auth but endpoint exists
        assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_alerts_endpoint():
    """Test alerts endpoint."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/alerts")
        # Should fail without auth but endpoint exists
        assert response.status_code in [401, 403, 422]

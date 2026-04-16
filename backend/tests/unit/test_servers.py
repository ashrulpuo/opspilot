"""Unit tests for server management endpoints."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.skip(
    reason="Legacy tests expect a wired ASGI client and DB overrides; add ASGITransport + get_db override before enabling.",
)


@pytest.mark.unit
class TestServerEndpoints:
    """Test server management endpoints."""

    async def test_create_server(self, client: AsyncClient, auth_headers):
        """Test creating a server."""
        response = await client.post(
            "/api/v1/organizations/test-org/servers",
            json={
                "hostname": "test-server",
                "ip_address": "192.168.1.100",
                "port": 22,
                "description": "Test server",
                "tags": ["test", "dev"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["hostname"] == "test-server"
        assert data["ip_address"] == "192.168.1.100"
        assert "id" in data

    async def test_list_servers(self, client: AsyncClient, auth_headers):
        """Test listing servers."""
        response = await client.get(
            "/api/v1/servers",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_get_server_by_id(self, client: AsyncClient, auth_headers):
        """Test getting a server by ID."""
        # First create a server
        create_response = await client.post(
            "/api/v1/organizations/test-org/servers",
            json={
                "hostname": "get-server",
                "ip_address": "192.168.1.101",
                "port": 22,
            },
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]

        # Get server
        response = await client.get(
            f"/api/v1/servers/{server_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == server_id
        assert data["hostname"] == "get-server"

    async def test_update_server(self, client: AsyncClient, auth_headers):
        """Test updating a server."""
        # First create a server
        create_response = await client.post(
            "/api/v1/organizations/test-org/servers",
            json={
                "hostname": "update-server",
                "ip_address": "192.168.1.102",
                "port": 22,
            },
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]

        # Update server
        response = await client.put(
            f"/api/v1/servers/{server_id}",
            json={
                "hostname": "updated-server",
                "description": "Updated description",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hostname"] == "updated-server"
        assert data["description"] == "Updated description"

    async def test_delete_server(self, client: AsyncClient, auth_headers):
        """Test deleting a server."""
        # First create a server
        create_response = await client.post(
            "/api/v1/organizations/test-org/servers",
            json={
                "hostname": "delete-server",
                "ip_address": "192.168.1.103",
                "port": 22,
            },
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]

        # Delete server
        response = await client.delete(
            f"/api/v1/servers/{server_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify server is deleted
        get_response = await client.get(
            f"/api/v1/servers/{server_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_create_server_missing_required_fields(self, client: AsyncClient, auth_headers):
        """Test creating a server with missing required fields."""
        response = await client.post(
            "/api/v1/organizations/test-org/servers",
            json={
                "hostname": "test-server",
                # Missing ip_address
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_get_nonexistent_server(self, client: AsyncClient, auth_headers):
        """Test getting a non-existent server."""
        response = await client.get(
            "/api/v1/servers/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

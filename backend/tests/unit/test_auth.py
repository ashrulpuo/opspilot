"""Unit tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePassword123!",
                "password_confirm": "SecurePassword123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_passwords_do_not_match(self, client: AsyncClient):
        """Test registration with mismatched passwords."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test2@example.com",
                "password": "Password123!",
                "password_confirm": "DifferentPassword123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 400

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "full_name": "Test User",
            },
        )

        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 400

    async def test_login_valid_credentials(self, client: AsyncClient):
        """Test login with valid credentials."""
        # First, register a user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "full_name": "Test User",
            },
        )

        # Now login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient):
        """Test getting current authenticated user."""
        # First, register and login
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "current@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "full_name": "Test User",
            },
        )
        token = register_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"
        assert data["full_name"] == "Test User"

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient):
        """Test refreshing access token."""
        # First, register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "full_name": "Test User",
            },
        )
        refresh_token = register_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refreshing with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401

    async def test_logout(self, client: AsyncClient):
        """Test logout."""
        # First, register and login
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "full_name": "Test User",
            },
        )
        token = register_response.json()["access_token"]

        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

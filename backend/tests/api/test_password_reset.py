"""Tests for password reset functionality."""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.main import app
from app.models.user import User
from app.models.password_reset import PasswordReset
from app.core.security import get_password_hash


@pytest.fixture
def test_password_reset(db_session):
    """Create a test password reset token."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create test user
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create password reset token
        password_reset = PasswordReset(
            user_id=user.id,
            token="test-token-1234567890abcdef",
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            used=False
        )
        session.add(password_reset)
        await session.commit()
        
        return {
            "user": user,
            "password_reset": password_reset
        }


@pytest.mark.asyncio
async def test_forgot_password_success(test_password_reset):
    """Test successful password reset request."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={
                "email": "test@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Don't reveal if email exists (security)
        assert "If an account with this email exists" in data["message"]


@pytest.mark.asyncio
async def test_forgot_password_rate_limiting(test_password_reset):
    """Test rate limiting for password reset."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send 4 requests rapidly (should fail on 4th)
        for i in range(4):
            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={
                    "email": "test@example.com"
                }
            )
            
            if i < 3:
                assert response.status_code == 200
            else:
                assert response.status_code == 429  # Too Many Requests


@pytest.mark.asyncio
async def test_reset_password_success(test_password_reset):
    """Test successful password reset."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "test-token-1234567890abcdef",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Password reset successfully" in data["message"]


@pytest.mark.asyncio
async def test_reset_password_invalid_token(test_password_reset):
    """Test password reset with invalid token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Invalid or expired reset token" in data["detail"]


@pytest.mark.asyncio
async def test_reset_password_expired_token(test_password_reset, db_session):
    """Test password reset with expired token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create expired token
        user = test_password_reset["user"]
        expired_reset = PasswordReset(
            user_id=user.id,
            token="expired-token-1234567890",
            expires_at=datetime.utcnow() - timedelta(minutes=5),  # Expired 5 minutes ago
            used=False
        )
        async with db_session() as session:
            session.add(expired_reset)
            await session.commit()
        
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "expired-token-1234567890",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Reset token has expired" in data["detail"]


@pytest.mark.asyncio
async def test_reset_password_already_used_token(test_password_reset):
    """Test password reset with already used token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Mark token as used
        password_reset_obj = test_password_reset["password_reset"]
        password_reset_obj.used = True
        
        async with db_session() as session:
            session.add(password_reset_obj)
            await session.commit()
        
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "test-token-1234567890abcdef",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "This reset token has already been used" in data["detail"]


@pytest.mark.asyncio
async def test_password_validation_rules():
    """Test password reset validation rules."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test missing token
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 422  # Validation Error
        
        # Test missing new_password
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "test-token-1234567890abcdef"
            }
        )
        assert response.status_code == 422  # Validation Error
        
        # Test short password
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "test-token-1234567890abcdef",
                "new_password": "short"
            }
        )
        assert response.status_code == 422  # Validation Error
        
        # Test missing new_password
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "test-token-1234567890abcdef",
                "new_password": "longenough"
            }
        )
        assert response.status_code == 422  # Validation Error

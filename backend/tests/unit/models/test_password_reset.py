"""Unit tests for Password Reset model."""
import pytest
from datetime import datetime, timedelta
from app.models.password_reset import PasswordReset
from app.models.user import User


@pytest.mark.unit
class TestPasswordResetModel:
    """Test PasswordReset model functionality."""

    def test_password_reset_creation(self):
        """Test password reset creation with valid data."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset = PasswordReset(
            user=user,
            token="test-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert password_reset.user == user
        assert password_reset.token == "test-token"
        assert password_reset.expires_at is not None
        assert password_reset.created_at is not None
        assert password_reset.updated_at is not None

    def test_password_reset_str_representation(self):
        """Test string representation of PasswordReset model."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset = PasswordReset(
            user=user,
            token="test-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert str(password_reset) == "PasswordReset(user='Test User', token='test-token')"

    def test_password_reset_equality(self):
        """Test password reset equality comparison."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset1 = PasswordReset(
            user=user,
            token="test-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        password_reset2 = PasswordReset(
            user=user,
            token="test-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert password_reset1 == password_reset2

    def test_password_reset_inequality(self):
        """Test password reset inequality comparison."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset1 = PasswordReset(
            user=user,
            token="test-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        password_reset2 = PasswordReset(
            user=user,
            token="different-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert password_reset1 != password_reset2

    def test_password_reset_default_values(self):
        """Test default values for PasswordReset model."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset = PasswordReset(
            user=user,
            token="test-token"
        )
        
        assert password_reset.expires_at is not None
        assert password_reset.created_at is not None
        assert password_reset.updated_at is not None

    def test_password_reset_with_user(self):
        """Test password reset with user relationship."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset = PasswordReset(
            user=user,
            token="test-token"
        )
        
        assert password_reset.user == user
        assert password_reset.user_id == user.id

    def test_password_reset_creation_without_optional_fields(self):
        """Test password reset creation without optional fields."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        password_reset = PasswordReset(
            user=user,
            token="test-token"
        )
        
        assert password_reset.user == user
        assert password_reset.token == "test-token"
        assert password_reset.expires_at is not None
        assert password_reset.created_at is not None
        assert password_reset.updated_at is not None

    def test_password_reset_expires_at_field(self):
        """Test password reset expires_at field."""
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        expires_at = datetime.utcnow() + timedelta(hours=1)
        password_reset = PasswordReset(
            user=user,
            token="test-token",
            expires_at=expires_at
        )
        
        assert password_reset.expires_at == expires_at
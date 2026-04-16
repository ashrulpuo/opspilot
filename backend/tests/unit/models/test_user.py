"""Unit tests for User model."""
import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.core.security import get_password_hash, verify_password


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""

    def test_user_creation(self):
        """Test user creation with valid data."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("securepassword123"),
            is_active=True,
            is_superuser=False
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "securepassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_user_str_representation(self):
        """Test string representation of User model."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        assert str(user) == "User(email='test@example.com', full_name='Test User')"

    def test_user_equality(self):
        """Test user equality comparison."""
        user1 = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        user2 = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        assert user1 == user2

    def test_user_inequality(self):
        """Test user inequality comparison."""
        user1 = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        user2 = User(
            email="different@example.com",
            full_name="Different User",
            hashed_password=get_password_hash("password")
        )
        
        assert user1 != user2

    def test_user_default_values(self):
        """Test default values for User model."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_password_validation(self):
        """Test password validation."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("SecurePassword123!")
        )
        
        assert len(user.hashed_password) > 0
        assert user.hashed_password != "SecurePassword123!"

    def test_user_update(self):
        """Test user update functionality."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        original_updated_at = user.updated_at
        
        # Simulate update
        user.full_name = "Updated User"
        user.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert user.full_name == "Updated User"
        assert user.updated_at > original_updated_at

    def test_user_deactivation(self):
        """Test user deactivation."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password"),
            is_active=True
        )
        
        user.is_active = False
        assert user.is_active is False

    def test_superuser_flag(self):
        """Test superuser flag."""
        user = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=get_password_hash("password"),
            is_superuser=True
        )
        
        assert user.is_superuser is True

    def test_user_creation_without_optional_fields(self):
        """Test user creation without optional fields."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password")
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.hashed_password is not None
        assert user.is_active is True
        assert user.is_superuser is False
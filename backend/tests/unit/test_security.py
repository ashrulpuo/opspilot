"""Unit tests for security utilities."""
import pytest
from app.core.security import get_password_hash, verify_password


@pytest.mark.unit
class TestSecurityUtilities:
    """Test security utility functions."""

    def test_password_hashing(self):
        """Test password hashing."""
        password = "securepassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_password_verification_valid(self):
        """Test password verification with valid credentials."""
        password = "securepassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_password_verification_invalid(self):
        """Test password verification with invalid credentials."""
        password = "securepassword123"
        hashed = get_password_hash("differentpassword")
        
        assert verify_password(password, hashed) is False

    def test_password_verification_empty_string(self):
        """Test password verification with empty string."""
        password = "securepassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False

    def test_password_hashing_different_passwords(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2

    def test_password_hashing_same_password_same_hash(self):
        """Test that same password produces same hash."""
        password = "samepassword"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 == hash2

    def test_password_verification_with_special_characters(self):
        """Test password verification with special characters."""
        password = "P@$$w0rd!123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_password_verification_with_numbers(self):
        """Test password verification with numbers."""
        password = "123456789"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_password_hashing_with_unicode(self):
        """Test password hashing with unicode characters."""
        password = "пароль123"  # Russian word for password
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert verify_password(password, hashed) is True

    def test_password_verification_case_sensitivity(self):
        """Test password verification case sensitivity."""
        password = "Password123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("password123", hashed) is False  # Different case

    def test_empty_password_hashing(self):
        """Test password hashing with empty string."""
        password = ""
        hashed = get_password_hash(password)
        
        assert hashed is not None

    def test_long_password_hashing(self):
        """Test password hashing with long password."""
        password = "a" * 100  # 100 character password
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert verify_password(password, hashed) is True
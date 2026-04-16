"""Unit tests for User model (aligned with `app.models.user.User`)."""
import pytest

from app.core.security import get_password_hash, verify_password
from app.models.user import User


@pytest.mark.unit
def test_user_construct_minimal() -> None:
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("securepassword123"),
        is_active=True,
    )
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True


@pytest.mark.unit
def test_user_password_roundtrip() -> None:
    raw = "another-secure-pass"
    user = User(
        email="u2@example.com",
        full_name="U2",
        password_hash=get_password_hash(raw),
    )
    assert verify_password(raw, user.password_hash) is True
    assert verify_password("wrong", user.password_hash) is False

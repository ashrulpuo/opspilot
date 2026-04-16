"""Tests for password reset model (no live HTTP — avoids duplicate routers / DB coupling)."""
from datetime import datetime, timedelta

import pytest

from app.models.password_reset import PasswordReset


@pytest.mark.unit
def test_password_reset_is_valid_when_fresh() -> None:
    pr = PasswordReset(
        user_id="user-1",
        token="x" * 32,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
    )
    assert pr.is_valid() is True


@pytest.mark.unit
def test_password_reset_is_invalid_when_used() -> None:
    pr = PasswordReset(
        user_id="user-1",
        token="x" * 32,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=True,
    )
    assert pr.is_valid() is False


@pytest.mark.unit
def test_password_reset_is_invalid_when_expired() -> None:
    pr = PasswordReset(
        user_id="user-1",
        token="x" * 32,
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        used=False,
    )
    assert pr.is_valid() is False


@pytest.mark.unit
def test_password_reset_repr() -> None:
    pr = PasswordReset(
        user_id="user-1",
        token="x" * 32,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
    )
    assert "PasswordReset" in repr(pr)

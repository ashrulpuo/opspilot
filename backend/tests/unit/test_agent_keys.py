"""Unit tests for per-server agent API key hashing."""
import pytest

from app.core.agent_keys import generate_agent_api_key, hash_agent_api_key, verify_agent_api_key


@pytest.mark.unit
def test_generate_agent_api_key_length() -> None:
    k = generate_agent_api_key()
    assert len(k) >= 32


@pytest.mark.unit
def test_hash_verify_roundtrip() -> None:
    plain = generate_agent_api_key()
    h = hash_agent_api_key(plain)
    assert verify_agent_api_key(plain, h) is True
    assert verify_agent_api_key("wrong", h) is False


@pytest.mark.unit
def test_verify_empty_hash() -> None:
    assert verify_agent_api_key("x", None) is False
    assert verify_agent_api_key("x", "") is False

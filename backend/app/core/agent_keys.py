"""Per-server agent API key generation and verification."""
from __future__ import annotations

import secrets

from passlib.hash import argon2


def generate_agent_api_key() -> str:
    """Return a high-entropy secret for X-API-Key (plaintext only at issuance / on host)."""
    return secrets.token_urlsafe(32)


def hash_agent_api_key(plain: str) -> str:
    """Hash a plaintext agent key for storage on the Server row."""
    return argon2.hash(plain)


def verify_agent_api_key(plain: str, stored_hash: str | None) -> bool:
    """Constant-time verify against stored Argon2 hash."""
    if not plain or not stored_hash:
        return False
    try:
        return argon2.verify(plain, stored_hash)
    except (ValueError, TypeError):
        return False

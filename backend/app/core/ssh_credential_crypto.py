"""Encrypt/decrypt server SSH passwords at rest (Fernet, key derived from SECRET_KEY).

Rotating ``SECRET_KEY`` invalidates existing ``ssh_password_encrypted`` values unless you
re-encrypt; plan key rotation accordingly for production.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _fernet() -> Fernet:
    raw = hashlib.sha256(get_settings().SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)


def encrypt_ssh_password(plaintext: str) -> str:
    """Encrypt SSH password for storage on ``servers.ssh_password_encrypted``."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_ssh_password(token: str) -> str:
    """Decrypt stored SSH password (internal / server-side only)."""
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Invalid or corrupted SSH credential blob") from e

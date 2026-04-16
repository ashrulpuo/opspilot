"""SSH credential Fernet helpers."""
import pytest

from app.core.ssh_credential_crypto import decrypt_ssh_password, encrypt_ssh_password


@pytest.mark.unit
def test_encrypt_decrypt_roundtrip() -> None:
    t = encrypt_ssh_password("my-s3cret!")
    assert t != "my-s3cret!"
    assert decrypt_ssh_password(t) == "my-s3cret!"


@pytest.mark.unit
def test_decrypt_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Invalid or corrupted"):
        decrypt_ssh_password("not-a-fernet-token")

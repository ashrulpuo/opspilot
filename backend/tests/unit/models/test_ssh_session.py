"""Unit tests for SSH session model (`SSHSesion` in `app.models.ssh_session`)."""
import uuid

import pytest

from app.models.ssh_session import SSHSesion


@pytest.mark.unit
def test_ssh_session_tablename() -> None:
    assert SSHSesion.__tablename__ == "ssh_sessions"


@pytest.mark.unit
def test_ssh_session_construct_minimal() -> None:
    sess = SSHSesion(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        server_id=str(uuid.uuid4()),
        organization_id=str(uuid.uuid4()),
        status="active",
    )
    assert sess.client_id is None
    assert sess.terminated_at is None
    assert sess.terminated_reason is None

"""Unit tests for command execution model (`Command` in `app.models.execution`)."""
import uuid

import pytest

from app.models.execution import Command


@pytest.mark.unit
def test_command_tablename() -> None:
    assert Command.__tablename__ == "commands"


@pytest.mark.unit
def test_command_repr() -> None:
    cid = uuid.uuid4()
    sid = uuid.uuid4()
    oid = uuid.uuid4()
    uid = uuid.uuid4()
    cmd = Command(
        id=cid,
        server_id=sid,
        organization_id=oid,
        user_id=uid,
        command="uptime",
        status="pending",
        created_at="2026-01-01",
        updated_at="2026-01-01",
    )
    assert "pending" in repr(cmd)

"""Smoke tests for Alert model."""
import uuid

import pytest

from app.models.alert import Alert


@pytest.mark.unit
def test_alert_construct() -> None:
    a = Alert(
        id=str(uuid.uuid4()),
        organization_id=str(uuid.uuid4()),
        server_id=str(uuid.uuid4()),
        type="cpu",
        threshold=90.0,
        value=95.0,
        status="open",
    )
    assert a.type == "cpu"
    assert a.status == "open"

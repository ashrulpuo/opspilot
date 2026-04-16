"""Unit tests for Server model (aligned with `app.models.server.Server`)."""
import uuid

import pytest

from app.models.organization import Organization
from app.models.server import Server


@pytest.mark.unit
def test_server_construct_minimal() -> None:
    org_id = str(uuid.uuid4())
    org = Organization(id=org_id, name="Acme", slug="acme")
    server = Server(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        hostname="web1.example.com",
        ip_address="10.0.0.1",
        os_type="linux",
        status="active",
    )
    assert server.hostname == "web1.example.com"
    assert server.organization_id == org_id
    assert server.status == "active"

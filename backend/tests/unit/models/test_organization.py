"""Smoke tests for Organization model."""
import uuid

import pytest

from app.models.organization import Organization


@pytest.mark.unit
def test_organization_construct() -> None:
    org = Organization(id=str(uuid.uuid4()), name="Acme Corp", slug="acme-corp")
    assert org.name == "Acme Corp"
    assert org.slug == "acme-corp"

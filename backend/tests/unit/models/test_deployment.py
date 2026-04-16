"""Smoke tests for deployment models."""
import pytest

from app.models.deployment import Deployment


@pytest.mark.unit
def test_deployment_tablename() -> None:
    assert Deployment.__tablename__ == "deployments"

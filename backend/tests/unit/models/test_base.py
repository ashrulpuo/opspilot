"""Smoke tests for shared SQLAlchemy declarative `Base` (metadata registry)."""
import pytest

from app.models.base import Base


@pytest.mark.unit
def test_base_is_declarative_registry() -> None:
    assert hasattr(Base, "metadata")
    assert Base.metadata is not None

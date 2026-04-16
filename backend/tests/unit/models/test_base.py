"""Unit tests for Base model."""
import pytest
from datetime import datetime, timedelta
from app.models.base import Base


@pytest.mark.unit
class TestBaseModel:
    """Test Base model functionality."""

    def test_base_model_creation(self):
        """Test base model creation with valid data."""
        base = Base()
        
        assert base.id is not None
        assert base.created_at is not None
        assert base.updated_at is not None

    def test_base_model_str_representation(self):
        """Test string representation of Base model."""
        base = Base()
        
        assert str(base).startswith("Base(id=")

    def test_base_model_equality(self):
        """Test base model equality comparison."""
        base1 = Base()
        base2 = Base()
        
        # Different IDs, so not equal
        assert base1 != base2

    def test_base_model_timestamps(self):
        """Test base model timestamps."""
        base = Base()
        
        assert base.created_at is not None
        assert base.updated_at is not None
        assert base.created_at <= base.updated_at

    def test_base_model_id_generation(self):
        """Test base model ID generation."""
        base = Base()
        
        assert base.id is not None
        assert isinstance(base.id, int)

    def test_base_model_creation_time(self):
        """Test base model creation time."""
        base = Base()
        
        # Check if created_at is recent
        from datetime import datetime, timedelta
        assert datetime.utcnow() - base.created_at < timedelta(seconds=1)
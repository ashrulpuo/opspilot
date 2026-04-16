"""Unit tests for Organization model."""
import pytest
from datetime import datetime, timedelta
from app.models.organization import Organization


@pytest.mark.unit
class TestOrganizationModel:
    """Test Organization model functionality."""

    def test_organization_creation(self):
        """Test organization creation with valid data."""
        org = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        assert org.name == "Test Organization"
        assert org.description == "Test organization description"
        assert org.is_active is True
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_str_representation(self):
        """Test string representation of Organization model."""
        org = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        assert str(org) == "Organization(name='Test Organization')"

    def test_organization_equality(self):
        """Test organization equality comparison."""
        org1 = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        org2 = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        assert org1 == org2

    def test_organization_inequality(self):
        """Test organization inequality comparison."""
        org1 = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        org2 = Organization(
            name="Different Organization",
            description="Different organization description"
        )
        
        assert org1 != org2

    def test_organization_default_values(self):
        """Test default values for Organization model."""
        org = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        assert org.is_active is True
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_update(self):
        """Test organization update functionality."""
        org = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        original_updated_at = org.updated_at
        
        # Simulate update
        org.description = "Updated organization description"
        org.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert org.description == "Updated organization description"
        assert org.updated_at > original_updated_at

    def test_organization_deactivation(self):
        """Test organization deactivation."""
        org = Organization(
            name="Test Organization",
            description="Test organization description",
            is_active=True
        )
        
        org.is_active = False
        assert org.is_active is False

    def test_organization_creation_without_optional_fields(self):
        """Test organization creation without optional fields."""
        org = Organization(
            name="Test Organization"
        )
        
        assert org.name == "Test Organization"
        assert org.description is None
        assert org.is_active is True
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_name_validation(self):
        """Test organization name validation."""
        org = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        assert org.name == "Test Organization"

    def test_organization_description_field(self):
        """Test organization description field."""
        org = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        
        assert org.description == "Test organization description"
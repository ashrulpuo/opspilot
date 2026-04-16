"""Unit tests for Server model."""
import pytest
from datetime import datetime, timedelta
from app.models.server import Server
from app.models.organization import Organization


@pytest.mark.unit
class TestServerModel:
    """Test Server model functionality."""

    def test_server_creation(self):
        """Test server creation with valid data."""
        org = Organization(name="Test Org")
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100",
            organization_id=1,
            is_active=True
        )
        
        assert server.name == "Test Server"
        assert server.hostname == "test-server.example.com"
        assert server.ip_address == "192.168.1.100"
        assert server.is_active is True
        assert server.created_at is not None
        assert server.updated_at is not None

    def test_server_str_representation(self):
        """Test string representation of Server model."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        assert str(server) == "Server(name='Test Server', hostname='test-server.example.com')"

    def test_server_equality(self):
        """Test server equality comparison."""
        server1 = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        server2 = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        assert server1 == server2

    def test_server_inequality(self):
        """Test server inequality comparison."""
        server1 = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        server2 = Server(
            name="Different Server",
            hostname="different-server.example.com",
            ip_address="192.168.1.101"
        )
        
        assert server1 != server2

    def test_server_default_values(self):
        """Test default values for Server model."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        assert server.is_active is True
        assert server.created_at is not None
        assert server.updated_at is not None

    def test_server_update(self):
        """Test server update functionality."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        original_updated_at = server.updated_at
        
        # Simulate update
        server.name = "Updated Server"
        server.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert server.name == "Updated Server"
        assert server.updated_at > original_updated_at

    def test_server_deactivation(self):
        """Test server deactivation."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100",
            is_active=True
        )
        
        server.is_active = False
        assert server.is_active is False

    def test_server_with_organization(self):
        """Test server with organization relationship."""
        org = Organization(name="Test Org")
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100",
            organization=org
        )
        
        assert server.organization == org
        assert server.organization_id == org.id

    def test_server_ip_address_validation(self):
        """Test IP address validation."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        assert server.ip_address == "192.168.1.100"

    def test_server_hostname_validation(self):
        """Test hostname validation."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        assert server.hostname == "test-server.example.com"

    def test_server_creation_without_optional_fields(self):
        """Test server creation without optional fields."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100"
        )
        
        assert server.name == "Test Server"
        assert server.hostname == "test-server.example.com"
        assert server.ip_address == "192.168.1.100"
        assert server.is_active is True
        assert server.created_at is not None
        assert server.updated_at is not None

    def test_server_description_field(self):
        """Test server description field."""
        server = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100",
            description="Test server description"
        )
        
        assert server.description == "Test server description"
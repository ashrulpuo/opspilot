"""Unit tests for Deployment model."""
import pytest
from datetime import datetime, timedelta
from app.models.deployment import Deployment
from app.models.server import Server
from app.models.user import User


@pytest.mark.unit
class TestDeploymentModel:
    """Test Deployment model functionality."""

    def test_deployment_creation(self):
        """Test deployment creation with valid data."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user,
            status="pending"
        )
        
        assert deployment.name == "Test Deployment"
        assert deployment.description == "Test deployment description"
        assert deployment.status == "pending"
        assert deployment.server == server
        assert deployment.user == user
        assert deployment.created_at is not None
        assert deployment.updated_at is not None

    def test_deployment_str_representation(self):
        """Test string representation of Deployment model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user,
            status="pending"
        )
        
        assert str(deployment) == "Deployment(name='Test Deployment', status='pending')"

    def test_deployment_equality(self):
        """Test deployment equality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment1 = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user,
            status="pending"
        )
        
        deployment2 = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user,
            status="pending"
        )
        
        assert deployment1 == deployment2

    def test_deployment_inequality(self):
        """Test deployment inequality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment1 = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user,
            status="pending"
        )
        
        deployment2 = Deployment(
            name="Different Deployment",
            description="Different deployment description",
            server=server,
            user=user,
            status="failed"
        )
        
        assert deployment1 != deployment2

    def test_deployment_default_values(self):
        """Test default values for Deployment model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user
        )
        
        assert deployment.status == "pending"
        assert deployment.created_at is not None
        assert deployment.updated_at is not None

    def test_deployment_update(self):
        """Test deployment update functionality."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user,
            status="pending"
        )
        
        original_updated_at = deployment.updated_at
        
        # Simulate update
        deployment.status = "completed"
        deployment.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert deployment.status == "completed"
        assert deployment.updated_at > original_updated_at

    def test_deployment_status_transitions(self):
        """Test deployment status transitions."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user
        )
        
        assert deployment.status == "pending"
        
        deployment.status = "running"
        assert deployment.status == "running"
        
        deployment.status = "completed"
        assert deployment.status == "completed"
        
        deployment.status = "failed"
        assert deployment.status == "failed"

    def test_deployment_with_server_and_user(self):
        """Test deployment with server and user relationships."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user
        )
        
        assert deployment.server == server
        assert deployment.user == user
        assert deployment.server_id == server.id
        assert deployment.user_id == user.id

    def test_deployment_creation_without_optional_fields(self):
        """Test deployment creation without optional fields."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            server=server,
            user=user
        )
        
        assert deployment.name == "Test Deployment"
        assert deployment.description is None
        assert deployment.status == "pending"
        assert deployment.server == server
        assert deployment.user == user
        assert deployment.created_at is not None
        assert deployment.updated_at is not None

    def test_deployment_description_field(self):
        """Test deployment description field."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        deployment = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            server=server,
            user=user
        )
        
        assert deployment.description == "Test deployment description"
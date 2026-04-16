"""Unit tests for Execution model."""
import pytest
from datetime import datetime, timedelta
from app.models.execution import Execution
from app.models.server import Server
from app.models.user import User


@pytest.mark.unit
class TestExecutionModel:
    """Test Execution model functionality."""

    def test_execution_creation(self):
        """Test execution creation with valid data."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user,
            status="pending"
        )
        
        assert execution.command == "ls -la"
        assert execution.status == "pending"
        assert execution.server == server
        assert execution.user == user
        assert execution.created_at is not None
        assert execution.updated_at is not None

    def test_execution_str_representation(self):
        """Test string representation of Execution model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user,
            status="pending"
        )
        
        assert str(execution) == "Execution(command='ls -la', status='pending')"

    def test_execution_equality(self):
        """Test execution equality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution1 = Execution(
            command="ls -la",
            server=server,
            user=user,
            status="pending"
        )
        
        execution2 = Execution(
            command="ls -la",
            server=server,
            user=user,
            status="pending"
        )
        
        assert execution1 == execution2

    def test_execution_inequality(self):
        """Test execution inequality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution1 = Execution(
            command="ls -la",
            server=server,
            user=user,
            status="pending"
        )
        
        execution2 = Execution(
            command="pwd",
            server=server,
            user=user,
            status="completed"
        )
        
        assert execution1 != execution2

    def test_execution_default_values(self):
        """Test default values for Execution model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user
        )
        
        assert execution.status == "pending"
        assert execution.created_at is not None
        assert execution.updated_at is not None

    def test_execution_update(self):
        """Test execution update functionality."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user,
            status="pending"
        )
        
        original_updated_at = execution.updated_at
        
        # Simulate update
        execution.status = "running"
        execution.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert execution.status == "running"
        assert execution.updated_at > original_updated_at

    def test_execution_status_transitions(self):
        """Test execution status transitions."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user
        )
        
        assert execution.status == "pending"
        
        execution.status = "running"
        assert execution.status == "running"
        
        execution.status = "completed"
        assert execution.status == "completed"
        
        execution.status = "failed"
        assert execution.status == "failed"

    def test_execution_with_server_and_user(self):
        """Test execution with server and user relationships."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user
        )
        
        assert execution.server == server
        assert execution.user == user
        assert execution.server_id == server.id
        assert execution.user_id == user.id

    def test_execution_creation_without_optional_fields(self):
        """Test execution creation without optional fields."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user
        )
        
        assert execution.command == "ls -la"
        assert execution.status == "pending"
        assert execution.server == server
        assert execution.user == user
        assert execution.created_at is not None
        assert execution.updated_at is not None

    def test_execution_output_field(self):
        """Test execution output field."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        execution = Execution(
            command="ls -la",
            server=server,
            user=user,
            output="test output"
        )
        
        assert execution.output == "test output"
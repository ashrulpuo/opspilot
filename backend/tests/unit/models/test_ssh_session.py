"""Unit tests for SSH Session model."""
import pytest
from datetime import datetime, timedelta
from app.models.ssh_session import SSHSession
from app.models.server import Server
from app.models.user import User


@pytest.mark.unit
class TestSSHSessionModel:
    """Test SSHSession model functionality."""

    def test_ssh_session_creation(self):
        """Test SSH session creation with valid data."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user,
            status="connected"
        )
        
        assert ssh_session.server == server
        assert ssh_session.user == user
        assert ssh_session.status == "connected"
        assert ssh_session.created_at is not None
        assert ssh_session.updated_at is not None

    def test_ssh_session_str_representation(self):
        """Test string representation of SSHSession model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user,
            status="connected"
        )
        
        assert str(ssh_session) == "SSHSession(server='Test Server', status='connected')"

    def test_ssh_session_equality(self):
        """Test SSH session equality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session1 = SSHSession(
            server=server,
            user=user,
            status="connected"
        )
        
        ssh_session2 = SSHSession(
            server=server,
            user=user,
            status="connected"
        )
        
        assert ssh_session1 == ssh_session2

    def test_ssh_session_inequality(self):
        """Test SSH session inequality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session1 = SSHSession(
            server=server,
            user=user,
            status="connected"
        )
        
        ssh_session2 = SSHSession(
            server=server,
            user=user,
            status="disconnected"
        )
        
        assert ssh_session1 != ssh_session2

    def test_ssh_session_default_values(self):
        """Test default values for SSHSession model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user
        )
        
        assert ssh_session.status == "connected"
        assert ssh_session.created_at is not None
        assert ssh_session.updated_at is not None

    def test_ssh_session_update(self):
        """Test SSH session update functionality."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user,
            status="connected"
        )
        
        original_updated_at = ssh_session.updated_at
        
        # Simulate update
        ssh_session.status = "disconnected"
        ssh_session.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert ssh_session.status == "disconnected"
        assert ssh_session.updated_at > original_updated_at

    def test_ssh_session_status_transitions(self):
        """Test SSH session status transitions."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user
        )
        
        assert ssh_session.status == "connected"
        
        ssh_session.status = "disconnected"
        assert ssh_session.status == "disconnected"
        
        ssh_session.status = "reconnecting"
        assert ssh_session.status == "reconnecting"

    def test_ssh_session_with_server_and_user(self):
        """Test SSH session with server and user relationships."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user
        )
        
        assert ssh_session.server == server
        assert ssh_session.user == user
        assert ssh_session.server_id == server.id
        assert ssh_session.user_id == user.id

    def test_ssh_session_creation_without_optional_fields(self):
        """Test SSH session creation without optional fields."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user
        )
        
        assert ssh_session.server == server
        assert ssh_session.user == user
        assert ssh_session.status == "connected"
        assert ssh_session.created_at is not None
        assert ssh_session.updated_at is not None

    def test_ssh_session_session_id_field(self):
        """Test SSH session session ID field."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        ssh_session = SSHSession(
            server=server,
            user=user,
            session_id="test-session-id"
        )
        
        assert ssh_session.session_id == "test-session-id"
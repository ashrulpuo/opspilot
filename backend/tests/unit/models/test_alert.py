"""Unit tests for Alert model."""
import pytest
from datetime import datetime, timedelta
from app.models.alert import Alert
from app.models.server import Server
from app.models.user import User


@pytest.mark.unit
class TestAlertModel:
    """Test Alert model functionality."""

    def test_alert_creation(self):
        """Test alert creation with valid data."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        assert alert.title == "Test Alert"
        assert alert.description == "Test alert description"
        assert alert.severity == "high"
        assert alert.status == "open"
        assert alert.server == server
        assert alert.user == user
        assert alert.created_at is not None
        assert alert.updated_at is not None

    def test_alert_str_representation(self):
        """Test string representation of Alert model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        assert str(alert) == "Alert(title='Test Alert', severity='high', status='open')"

    def test_alert_equality(self):
        """Test alert equality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert1 = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        alert2 = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        assert alert1 == alert2

    def test_alert_inequality(self):
        """Test alert inequality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert1 = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        alert2 = Alert(
            title="Different Alert",
            description="Different alert description",
            server=server,
            user=user,
            severity="medium",
            status="closed"
        )
        
        assert alert1 != alert2

    def test_alert_default_values(self):
        """Test default values for Alert model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high"
        )
        
        assert alert.status == "open"
        assert alert.created_at is not None
        assert alert.updated_at is not None

    def test_alert_update(self):
        """Test alert update functionality."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        original_updated_at = alert.updated_at
        
        # Simulate update
        alert.status = "closed"
        alert.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert alert.status == "closed"
        assert alert.updated_at > original_updated_at

    def test_alert_status_transitions(self):
        """Test alert status transitions."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high"
        )
        
        assert alert.status == "open"
        
        alert.status = "acknowledged"
        assert alert.status == "acknowledged"
        
        alert.status = "closed"
        assert alert.status == "closed"

    def test_alert_severity_levels(self):
        """Test alert severity levels."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high",
            status="open"
        )
        
        assert alert.severity == "high"
        
        alert.severity = "medium"
        assert alert.severity == "medium"
        
        alert.severity = "low"
        assert alert.severity == "low"

    def test_alert_with_server_and_user(self):
        """Test alert with server and user relationships."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high"
        )
        
        assert alert.server == server
        assert alert.user == user
        assert alert.server_id == server.id
        assert alert.user_id == user.id

    def test_alert_creation_without_optional_fields(self):
        """Test alert creation without optional fields."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            server=server,
            user=user,
            severity="high"
        )
        
        assert alert.title == "Test Alert"
        assert alert.description is None
        assert alert.severity == "high"
        assert alert.status == "open"
        assert alert.server == server
        assert alert.user == user
        assert alert.created_at is not None
        assert alert.updated_at is not None

    def test_alert_description_field(self):
        """Test alert description field."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        alert = Alert(
            title="Test Alert",
            description="Test alert description",
            server=server,
            user=user,
            severity="high"
        )
        
        assert alert.description == "Test alert description"
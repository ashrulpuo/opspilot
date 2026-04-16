"""Unit tests for Backup model."""
import pytest
from datetime import datetime, timedelta
from app.models.backup import Backup
from app.models.server import Server
from app.models.user import User


@pytest.mark.unit
class TestBackupModel:
    """Test Backup model functionality."""

    def test_backup_creation(self):
        """Test backup creation with valid data."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user,
            status="pending"
        )
        
        assert backup.name == "Test Backup"
        assert backup.description == "Test backup description"
        assert backup.status == "pending"
        assert backup.server == server
        assert backup.user == user
        assert backup.created_at is not None
        assert backup.updated_at is not None

    def test_backup_str_representation(self):
        """Test string representation of Backup model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user,
            status="pending"
        )
        
        assert str(backup) == "Backup(name='Test Backup', status='pending')"

    def test_backup_equality(self):
        """Test backup equality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup1 = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user,
            status="pending"
        )
        
        backup2 = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user,
            status="pending"
        )
        
        assert backup1 == backup2

    def test_backup_inequality(self):
        """Test backup inequality comparison."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup1 = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user,
            status="pending"
        )
        
        backup2 = Backup(
            name="Different Backup",
            description="Different backup description",
            server=server,
            user=user,
            status="failed"
        )
        
        assert backup1 != backup2

    def test_backup_default_values(self):
        """Test default values for Backup model."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user
        )
        
        assert backup.status == "pending"
        assert backup.created_at is not None
        assert backup.updated_at is not None

    def test_backup_update(self):
        """Test backup update functionality."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user,
            status="pending"
        )
        
        original_updated_at = backup.updated_at
        
        # Simulate update
        backup.status = "completed"
        backup.updated_at = datetime.utcnow() + timedelta(seconds=1)
        
        assert backup.status == "completed"
        assert backup.updated_at > original_updated_at

    def test_backup_status_transitions(self):
        """Test backup status transitions."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user
        )
        
        assert backup.status == "pending"
        
        backup.status = "running"
        assert backup.status == "running"
        
        backup.status = "completed"
        assert backup.status == "completed"
        
        backup.status = "failed"
        assert backup.status == "failed"

    def test_backup_with_server_and_user(self):
        """Test backup with server and user relationships."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user
        )
        
        assert backup.server == server
        assert backup.user == user
        assert backup.server_id == server.id
        assert backup.user_id == user.id

    def test_backup_creation_without_optional_fields(self):
        """Test backup creation without optional fields."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            server=server,
            user=user
        )
        
        assert backup.name == "Test Backup"
        assert backup.description is None
        assert backup.status == "pending"
        assert backup.server == server
        assert backup.user == user
        assert backup.created_at is not None
        assert backup.updated_at is not None

    def test_backup_description_field(self):
        """Test backup description field."""
        server = Server(name="Test Server", hostname="test-server.example.com", ip_address="192.168.1.100")
        user = User(email="test@example.com", full_name="Test User", hashed_password="hashed_password")
        
        backup = Backup(
            name="Test Backup",
            description="Test backup description",
            server=server,
            user=user
        )
        
        assert backup.description == "Test backup description"
#!/usr/bin/env python3
"""Direct model tests without config imports."""

import sys
import os
from unittest.mock import Mock
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Mock the problematic imports to avoid configuration issues
sys.modules['app.main'] = Mock()
sys.modules['app.api.v1'] = Mock()
sys.modules['app.services'] = Mock()
sys.modules['app.core'] = Mock()

# Mock the config module
sys.modules['app.core.config'] = Mock()
sys.modules['app.core.config'].Settings = Mock

def run_tests():
    """Run basic tests for all models."""
    print("Running model tests...")
    
    # Import models directly
    from app.models.user import User
    from app.models.server import Server
    from app.models.organization import Organization
    from app.models.deployment import Deployment
    from app.models.backup import Backup
    from app.models.alert import Alert
    from app.models.metrics import Metric
    from app.models.execution import Execution
    from app.models.ssh_session import SSHSession
    from app.models.password_reset import PasswordReset
    from app.models.base import Base
    from app.core.security import get_password_hash, verify_password

    # Test User model
    print("Testing User model...")
    user_test = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("securepassword123"),
        is_active=True,
        is_superuser=False
    )
    assert user_test.email == "test@example.com"
    assert verify_password("securepassword123", user_test.hashed_password)
    
    # Test Server model
    print("Testing Server model...")
    server_test = Server(
        name="Test Server",
        hostname="test-server.example.com",
        ip_address="192.168.1.100",
        is_active=True
    )
    assert server_test.name == "Test Server"
    
    # Test Organization model
    print("Testing Organization model...")
    org_test = Organization(
        name="Test Organization",
        description="Test organization description"
    )
    assert org_test.name == "Test Organization"
    
    # Test Deployment model
    print("Testing Deployment model...")
    deployment_test = Deployment(
        name="Test Deployment",
        description="Test deployment description",
        status="pending"
    )
    assert deployment_test.name == "Test Deployment"
    
    # Test Backup model
    print("Testing Backup model...")
    backup_test = Backup(
        name="Test Backup",
        description="Test backup description",
        status="pending"
    )
    assert backup_test.name == "Test Backup"
    
    # Test Alert model
    print("Testing Alert model...")
    alert_test = Alert(
        title="Test Alert",
        description="Test alert description",
        severity="high",
        status="open"
    )
    assert alert_test.title == "Test Alert"
    
    # Test Metrics model
    print("Testing Metrics model...")
    metrics_test = Metric(
        name="cpu_usage",
        value=75.5,
        unit="%",
    )
    assert metrics_test.name == "cpu_usage"
    
    # Test Execution model
    print("Testing Execution model...")
    execution_test = Execution(
        command="ls -la",
        status="pending"
    )
    assert execution_test.command == "ls -la"
    
    # Test SSH Session model
    print("Testing SSH Session model...")
    ssh_session_test = SSHSession(
        status="connected"
    )
    assert ssh_session_test.status == "connected"
    
    # Test Password Reset model
    print("Testing Password Reset model...")
    password_reset_test = PasswordReset(
        token="test-token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    assert password_reset_test.token == "test-token"
    
    # Test Base model
    print("Testing Base model...")
    base_test = Base()
    assert base_test.id is not None
    
    print("All model tests passed!")

if __name__ == "__main__":
    run_tests()
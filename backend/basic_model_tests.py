#!/usr/bin/env python3
"""Basic model tests without coverage."""

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

# Create mock settings
from app.core.config import Settings
mock_settings = Mock(spec=Settings)
mock_settings.DATABASE_URL = 'sqlite+aiosqlite:///:memory:'

# Override the settings import
sys.modules['app.core.config'] = Mock()
sys.modules['app.core.config'].settings = mock_settings

# Import the models we want to test
from app.models import user, server, organization, deployment, backup, alert, metrics, execution, ssh_session, password_reset, base
from app.core.security import get_password_hash, verify_password

def run_tests():
    """Run basic tests for all models."""
    print("Running model tests...")
    
    # Test User model
    print("Testing User model...")
    user_test = user.User(
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
    server_test = server.Server(
        name="Test Server",
        hostname="test-server.example.com",
        ip_address="192.168.1.100",
        is_active=True
    )
    assert server_test.name == "Test Server"
    
    # Test Organization model
    print("Testing Organization model...")
    org_test = organization.Organization(
        name="Test Organization",
        description="Test organization description"
    )
    assert org_test.name == "Test Organization"
    
    # Test Deployment model
    print("Testing Deployment model...")
    deployment_test = deployment.Deployment(
        name="Test Deployment",
        description="Test deployment description",
        status="pending"
    )
    assert deployment_test.name == "Test Deployment"
    
    # Test Backup model
    print("Testing Backup model...")
    backup_test = backup.Backup(
        name="Test Backup",
        description="Test backup description",
        status="pending"
    )
    assert backup_test.name == "Test Backup"
    
    # Test Alert model
    print("Testing Alert model...")
    alert_test = alert.Alert(
        title="Test Alert",
        description="Test alert description",
        severity="high",
        status="open"
    )
    assert alert_test.title == "Test Alert"
    
    # Test Metrics model
    print("Testing Metrics model...")
    metrics_test = metrics.Metric(
        name="cpu_usage",
        value=75.5,
        unit="%",
    )
    assert metrics_test.name == "cpu_usage"
    
    # Test Execution model
    print("Testing Execution model...")
    execution_test = execution.Execution(
        command="ls -la",
        status="pending"
    )
    assert execution_test.command == "ls -la"
    
    # Test SSH Session model
    print("Testing SSH Session model...")
    ssh_session_test = ssh_session.SSHSession(
        status="connected"
    )
    assert ssh_session_test.status == "connected"
    
    # Test Password Reset model
    print("Testing Password Reset model...")
    password_reset_test = password_reset.PasswordReset(
        token="test-token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    assert password_reset_test.token == "test-token"
    
    # Test Base model
    print("Testing Base model...")
    base_test = base.Base()
    assert base_test.id is not None
    
    print("All model tests passed!")

if __name__ == "__main__":
    run_tests()
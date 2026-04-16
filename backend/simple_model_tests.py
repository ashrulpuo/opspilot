#!/usr/bin/env python3
"""Simple model tests with all dependencies mocked."""

import sys
import os
from unittest.mock import Mock
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Mock all problematic imports
sys.modules['app.main'] = Mock()
sys.modules['app.api.v1'] = Mock()
sys.modules['app.services'] = Mock()
sys.modules['app.core'] = Mock()
sys.modules['app.core.database'] = Mock()
sys.modules['app.core.config'] = Mock()
sys.modules['app.core.security'] = Mock()

# Mock the Base class from SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

def run_tests():
    """Run basic tests for all models."""
    print("Running model tests...")
    
    # Import models directly
    from app.models.user import User
    from app.models.server import Server
    from app.models.organization import Organization
    from app.models.deployment import Deployment
    from app.models.backup import BackupSchedule as Backup
    from app.models.alert import Alert
    from app.models.metrics import Metric
    from app.models.execution import Command as Execution
    from app.models.ssh_session import SSHSesion as SSHSession
    from app.models.password_reset import PasswordReset
    from app.models.base import Base as ModelBase
    from app.core.security import get_password_hash, verify_password

    # Test User model
    print("Testing User model...")
    user_test = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False
    )
    
    # Test Server model
    print("Testing Server model...")
    server_test = Server(
        name="Test Server",
        hostname="test-server.example.com",
        ip_address="192.168.1.100",
        is_active=True
    )
    
    # Test Organization model
    print("Testing Organization model...")
    org_test = Organization(
        name="Test Organization",
        description="Test organization description"
    )
    
    # Test Deployment model
    print("Testing Deployment model...")
    deployment_test = Deployment(
        name="Test Deployment",
        description="Test deployment description",
        status="pending"
    )
    
    # Test Backup model
    print("Testing Backup model...")
    backup_test = Backup(
        name="Test Backup",
        description="Test backup description",
        status="pending"
    )
    
    # Test Alert model
    print("Testing Alert model...")
    alert_test = Alert(
        title="Test Alert",
        description="Test alert description",
        severity="high",
        status="open"
    )
    
    # Test Metrics model
    print("Testing Metrics model...")
    metrics_test = Metric(
        name="cpu_usage",
        value=75.5,
        unit="%",
    )
    
    # Test Execution model
    print("Testing Execution model...")
    execution_test = Execution(
        command="ls -la",
        status="pending"
    )
    
    # Test SSH Session model
    print("Testing SSH Session model...")
    ssh_session_test = SSHSession(
        status="connected"
    )
    
    # Test Password Reset model
    print("Testing Password Reset model...")
    password_reset_test = PasswordReset(
        token="test-token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    
    # Test Base model
    print("Testing Base model...")
    base_test = ModelBase()
    
    print("All model tests passed!")

if __name__ == "__main__":
    run_tests()
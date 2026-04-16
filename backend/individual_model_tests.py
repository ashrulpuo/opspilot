#!/usr/bin/env python3
"""Individual model tests with all dependencies mocked."""

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
    """Run individual tests for each model."""
    print("Running individual model tests...")
    
    # Test User model
    print("Testing User model...")
    try:
        from app.models.user import User
        user_test = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False
        )
        print("User model test passed")
    except Exception as e:
        print(f"User model test failed: {e}")
    
    # Test Server model
    print("Testing Server model...")
    try:
        from app.models.server import Server
        server_test = Server(
            name="Test Server",
            hostname="test-server.example.com",
            ip_address="192.168.1.100",
            is_active=True
        )
        print("Server model test passed")
    except Exception as e:
        print(f"Server model test failed: {e}")
    
    # Test Organization model
    print("Testing Organization model...")
    try:
        from app.models.organization import Organization
        org_test = Organization(
            name="Test Organization",
            description="Test organization description"
        )
        print("Organization model test passed")
    except Exception as e:
        print(f"Organization model test failed: {e}")
    
    # Test Deployment model
    print("Testing Deployment model...")
    try:
        from app.models.deployment import Deployment
        deployment_test = Deployment(
            name="Test Deployment",
            description="Test deployment description",
            status="pending"
        )
        print("Deployment model test passed")
    except Exception as e:
        print(f"Deployment model test failed: {e}")
    
    # Test Backup model
    print("Testing Backup model...")
    try:
        from app.models.backup import BackupSchedule as Backup
        backup_test = Backup(
            name="Test Backup",
            description="Test backup description",
            status="pending"
        )
        print("Backup model test passed")
    except Exception as e:
        print(f"Backup model test failed: {e}")
    
    # Test Alert model
    print("Testing Alert model...")
    try:
        from app.models.alert import Alert
        alert_test = Alert(
            title="Test Alert",
            description="Test alert description",
            severity="high",
            status="open"
        )
        print("Alert model test passed")
    except Exception as e:
        print(f"Alert model test failed: {e}")
    
    # Test Metrics model
    print("Testing Metrics model...")
    try:
        from app.models.metrics import Metric
        metrics_test = Metric(
            name="cpu_usage",
            value=75.5,
            unit="%",
        )
        print("Metrics model test passed")
    except Exception as e:
        print(f"Metrics model test failed: {e}")
    
    # Test Execution model
    print("Testing Execution model...")
    try:
        from app.models.execution import Command as Execution
        execution_test = Execution(
            command="ls -la",
            status="pending"
        )
        print("Execution model test passed")
    except Exception as e:
        print(f"Execution model test failed: {e}")
    
    # Test SSH Session model
    print("Testing SSH Session model...")
    try:
        from app.models.ssh_session import SSHSesion as SSHSession
        ssh_session_test = SSHSession(
            status="connected"
        )
        print("SSH Session model test passed")
    except Exception as e:
        print(f"SSH Session model test failed: {e}")
    
    # Test Password Reset model
    print("Testing Password Reset model...")
    try:
        from app.models.password_reset import PasswordReset
        password_reset_test = PasswordReset(
            token="test-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        print("Password Reset model test passed")
    except Exception as e:
        print(f"Password Reset model test failed: {e}")
    
    # Test Base model
    print("Testing Base model...")
    try:
        from app.models.base import Base as ModelBase
        base_test = ModelBase()
        print("Base model test passed")
    except Exception as e:
        print(f"Base model test failed: {e}")
    
    print("All model tests completed!")

if __name__ == "__main__":
    run_tests()
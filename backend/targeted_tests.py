#!/usr/bin/env python3
"""Targeted test runner for specific module coverage."""

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Only mock specific problematic modules
sys.modules['app.main'] = Mock()
sys.modules['app.api.v1'] = Mock()
sys.modules['app.services'] = Mock()

def run_targeted_tests():
    """Run targeted tests for coverage improvement."""
    print("Running targeted tests for coverage improvement...")
    
    # Test security module
    print("\nTesting security module...")
    try:
        # Mock database dependency in security module
        with patch('app.core.security.Base') as mock_base:
            from app.core.security import get_password_hash, verify_password
            
            # Test password hashing
            password = "testpassword123"
            hashed = get_password_hash(password)
            assert hashed is not None and hashed != password
            
            # Test password verification
            assert verify_password(password, hashed) is True
            assert verify_password("wrongpassword", hashed) is False
            
            print("✓ Security module tests passed")
    except Exception as e:
        print(f"✗ Security module tests failed: {e}")
    
    # Test Vault client
    print("\nTesting Vault client...")
    try:
        # Mock httpx dependency
        with patch('app.core.vault.httpx') as mock_httpx:
            from app.core.vault import VaultClient
            
            vault_client = VaultClient()
            assert vault_client is not None
            
            # Test setting credentials
            vault_client.set_credentials("http://localhost:8200", "test-token")
            assert vault_client.url == "http://localhost:8200"
            assert vault_client.token == "test-token"
            
            print("✓ Vault client tests passed")
    except Exception as e:
        print(f"✗ Vault client tests failed: {e}")
    
    # Test Salt client
    print("\nTesting Salt client...")
    try:
        # Mock httpx dependency
        with patch('app.core.salt.httpx') as mock_httpx:
            from app.core.salt import SaltClient
            
            salt_client = SaltClient()
            assert salt_client is not None
            
            # Test setting credentials
            salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
            assert salt_client.base_url == "http://localhost:8000"
            assert salt_client.username == "saltapi"
            assert salt_client.password == "testpass"
            
            print("✓ Salt client tests passed")
    except Exception as e:
        print(f"✗ Salt client tests failed: {e}")
    
    # Test Email service
    print("\nTesting Email service...")
    try:
        # Mock jinja2 and httpx dependencies
        with patch('app.core.email.jinja2') as mock_jinja2, \
             patch('app.core.email.httpx') as mock_httpx:
            from app.core.email import email_service
            
            email_svc = email_service
            assert email_svc is not None
            
            # Test setting SMTP config
            email_svc.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
            assert email_svc.smtp_host == "smtp.example.com"
            assert email_svc.smtp_port == 587
            
            print("✓ Email service tests passed")
    except Exception as e:
        print(f"✗ Email service tests failed: {e}")
    
    # Test models that work without relationships
    print("\nTesting models without relationships...")
    try:
        # Mock database dependency
        with patch('app.models.user.Base') as mock_base:
            from app.models.user import User
            from app.models.server import Server
            from app.models.organization import Organization
            from app.models.alert import Alert
            from app.models.metrics import Metric
            from app.models.ssh_session import SSHSesion as SSHSession
            from app.models.base import Base as ModelBase
            
            # Test User model
            user = User(email="test@example.com", full_name="Test User", hashed_password="hash")
            assert user.email == "test@example.com"
            
            # Test Server model
            server = Server(name="Test Server", hostname="test.example.com", ip_address="192.168.1.100")
            assert server.name == "Test Server"
            
            # Test Organization model
            org = Organization(name="Test Org", description="Test description")
            assert org.name == "Test Org"
            
            # Test Alert model
            alert = Alert(title="Test Alert", description="Test alert", severity="high", status="open")
            assert alert.title == "Test Alert"
            
            # Test Metrics model
            metric = Metric(name="cpu_usage", value=75.5, unit="%")
            assert metric.name == "cpu_usage"
            
            # Test SSH Session model
            session = SSHSession(status="connected")
            assert session.status == "connected"
            
            # Test Base model
            base = ModelBase()
            assert base.id is not None
            
            print("✓ Model tests passed")
    except Exception as e:
        print(f"✗ Model tests failed: {e}")
    
    # Test config module
    print("\nTesting config module...")
    try:
        from app.core.config import Settings
        
        settings = Settings()
        assert settings is not None
        assert settings.API_V1_STR == "/api/v1"
        assert settings.PROJECT_NAME == "OpsPilot"
        
        print("✓ Config module tests passed")
    except Exception as e:
        print(f"✗ Config module tests failed: {e}")
    
    print("\n" + "="*50)
    print("Targeted tests completed!")
    print("="*50)

if __name__ == "__main__":
    run_targeted_tests()
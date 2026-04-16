#!/usr/bin/env python3
"""Run model tests without full application startup."""

import sys
import os
import pytest
from unittest.mock import Mock

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
mock_settings.SALT_MASTER_URL = 'localhost'
mock_settings.SALT_API_PORT = 8000
mock_settings.REDIS_URL = 'redis://localhost:6379/0'
mock_settings.vault_url = 'http://localhost:8200'
mock_settings.vault_token = 'test-token'
mock_settings.salt_api_url = 'http://localhost:8000'
mock_settings.salt_api_username = 'saltapi'
mock_settings.salt_api_password = 'saltapi'

# Override the settings import
sys.modules['app.core.config'] = Mock()
sys.modules['app.core.config'].settings = mock_settings

# Import the models we want to test
from app.models import user, server, organization, deployment, backup, alert, metrics, execution, ssh_session, password_reset, base
from app.core.security import get_password_hash, verify_password

# Run the tests
if __name__ == "__main__":
    # Discover and run tests in the models directory
    pytest_args = [
        'tests/unit/models',
        '--cov=app',
        '--cov-report=term-missing',
        '--cov-report=html',
        '-v'
    ]
    
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)
#!/usr/bin/env python3
"""Simple coverage analysis script."""

import coverage
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Start coverage
cov = coverage.Coverage(source=['app'], omit=["*/tests/*", "*/__pycache__/*", "*/migrations/*"])
cov.start()

# Import and test modules
try:
    # Test models
    print("Testing models...")
    from app.models import user, server, organization, deployment, backup, alert, metrics, execution, ssh_session, password_reset
    
    # Test core modules
    print("Testing core modules...")
    from app.core import security, config, database, salt, vault, email, exceptions
    
    # Test services
    print("Testing services...")
    from app.services import server_service, salt_service
    
    # Test API modules
    print("Testing API modules...")
    from app.api.v1 import auth, health, servers, organizations, metrics, backups, health_checks, ssh, dashboard, salt as api_salt, alerts, credentials, commands, logs, deployments
    
    print("All modules imported successfully!")
    
except Exception as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Stop coverage
cov.stop()
cov.save()

# Generate report
print("\nCoverage Report:")
cov.report()

# Generate HTML report
cov.html_report()

print("\nHTML report generated in htmlcov/ directory")
"""API v1 router."""
from fastapi import APIRouter

# Import all API modules
from app.api.v1 import health, auth, password_reset, servers, organizations, metrics, backups, health_checks, ssh, dashboard

# Security scan is temporarily disabled due to import issues
# from app.api.v1 import security_scan as security_scan_fixed

# Initialize API router
api_router = APIRouter()

# Include routers with proper tags
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(password_reset.router, tags=["Authentication"])
# api_router.include_router(security_scan_fixed.router, tags=["Security"])  # Temporarily disabled
api_router.include_router(servers.router, tags=["Servers"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(metrics.router, tags=["Metrics"])
api_router.include_router(backups.router, tags=["Backups"])
api_router.include_router(health_checks.router, tags=["Health Checks"])
api_router.include_router(ssh.router, tags=["SSH"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
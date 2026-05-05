"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import (
    health, auth, password_reset,
    servers, organizations, metrics, agent_data,
    backups, backups2, health_checks, ssh, dashboard,
    alerts, credentials, commands, deployments, logs,
    security_scan_fixed, stream, notification_settings,
    monitors,
    registry,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(password_reset.router, tags=["Authentication"])
api_router.include_router(servers.router, tags=["Servers"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(metrics.router, tags=["Metrics"])
api_router.include_router(agent_data.router, tags=["Agent data"])
api_router.include_router(backups.router, tags=["Backups"])
api_router.include_router(backups2.router, tags=["Backup Schedules"])
api_router.include_router(health_checks.router, tags=["Health Checks"])
api_router.include_router(ssh.router, tags=["SSH"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(credentials.router, tags=["Credentials"])
api_router.include_router(commands.router, tags=["Commands"])
api_router.include_router(deployments.router, tags=["Deployments"])
api_router.include_router(logs.router, tags=["Logs"])
api_router.include_router(security_scan_fixed.router, tags=["Security"])
api_router.include_router(stream.router, tags=["SSE"])
api_router.include_router(notification_settings.router, tags=["Notification Settings"])
api_router.include_router(monitors.router, tags=["Monitors"])
api_router.include_router(registry.router, tags=["Registry"])
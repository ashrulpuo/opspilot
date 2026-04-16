"""Dashboard API endpoints for OpsPilot."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.server import Server
from app.models.organization import Organization, OrganizationMember

router = APIRouter()


# Response Schemas
class DashboardStats(BaseModel):
    """Dashboard statistics response schema."""

    servers_total: int
    servers_online: int
    servers_offline: int
    organizations_total: int
    alerts_active: int
    alerts_critical: int
    commands_today: int


class ServerHealthOverview(BaseModel):
    """Server health overview response schema."""

    server_id: str
    server_name: str
    status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: int
    last_seen: str


class RecentAlert(BaseModel):
    """Recent alert response schema."""

    id: str
    server_name: str
    severity: str
    title: str
    message: str
    created_at: str


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get dashboard statistics.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Dashboard statistics
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Count servers
    servers_result = await db.execute(
        select(func.count(Server.id)).where(
            Server.organization_id.in_(org_ids) if org_ids else False
        )
    )
    servers_total = servers_result.scalar() or 0

    # Count online servers
    online_result = await db.execute(
        select(func.count(Server.id)).where(
            Server.organization_id.in_(org_ids) if org_ids else False,
            Server.status == "online"
        )
    )
    servers_online = online_result.scalar() or 0

    servers_offline = servers_total - servers_online

    # Count organizations
    org_count_result = await db.execute(
        select(func.count(Organization.id)).where(
            Organization.id.in_(org_ids) if org_ids else False
        )
    )
    organizations_total = org_count_result.scalar() or 0

    # TODO: Implement alerts and commands counting
    alerts_active = 0
    alerts_critical = 0
    commands_today = 0

    return DashboardStats(
        servers_total=servers_total,
        servers_online=servers_online,
        servers_offline=servers_offline,
        organizations_total=organizations_total,
        alerts_active=alerts_active,
        alerts_critical=alerts_critical,
        commands_today=commands_today,
    )


@router.get("/server-health", response_model=List[ServerHealthOverview])
async def get_server_health(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get server health overview.

    Args:
        limit: Maximum number of servers to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of server health information
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Get servers
    servers_query = (
        select(Server)
        .where(
            Server.organization_id.in_(org_ids) if org_ids else False
        )
        .order_by(Server.updated_at.desc())
        .limit(limit)
    )
    servers_result = await db.execute(servers_query)
    servers = servers_result.scalars().all()

    # Import Metrics model
    from app.models.metrics import Metrics

    # Build health overview with latest metrics
    health_overview = []
    for server in servers:
        # Get latest metrics for this server
        metrics_query = (
            select(Metrics)
            .where(Metrics.server_id == server.id)
            .order_by(Metrics.timestamp.desc())
            .limit(1)
        )
        metrics_result = await db.execute(metrics_query)
        latest_metrics = metrics_result.scalar_one_or_none()

        if latest_metrics:
            health_overview.append(
                ServerHealthOverview(
                    server_id=server.id,
                    server_name=server.hostname,
                    status=server.status,
                    cpu_usage=latest_metrics.cpu_usage_percent or 0.0,
                    memory_usage=latest_metrics.memory_usage_percent or 0.0,
                    disk_usage=latest_metrics.disk_usage_percent or 0.0,
                    uptime=latest_metrics.uptime_seconds or 0,
                    last_seen=server.updated_at.isoformat(),
                )
            )
        else:
            health_overview.append(
                ServerHealthOverview(
                    server_id=server.id,
                    server_name=server.hostname,
                    status=server.status,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    disk_usage=0.0,
                    uptime=0,
                    last_seen=server.updated_at.isoformat(),
                )
            )

    return health_overview


@router.get("/recent-alerts", response_model=List[RecentAlert])
async def get_recent_alerts(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get recent alerts.

    Args:
        limit: Maximum number of alerts to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of recent alerts
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # Import Alert model
    from app.models.alert import Alert

    # Get recent alerts
    alerts_query = (
        select(Alert, Server.hostname)
        .join(Server, Alert.server_id == Server.id)
        .where(
            Alert.organization_id.in_(org_ids) if org_ids else False,
            Alert.resolved == False,  # Only unresolved alerts
        )
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    alerts_result = await db.execute(alerts_query)
    alerts = alerts_result.fetchall()

    # Build recent alerts list
    recent_alerts = []
    for alert, hostname in alerts:
        recent_alerts.append(
            RecentAlert(
                id=alert.id,
                server_name=hostname,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                created_at=alert.created_at.isoformat(),
            )
        )

    return recent_alerts


# Import BaseModel
from pydantic import BaseModel

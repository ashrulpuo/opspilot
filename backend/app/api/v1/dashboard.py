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
from app.models.metrics import Metric
from app.models.alert import Alert

router = APIRouter()


async def _latest_metric_values(db: AsyncSession, server_id: str) -> Dict[str, float]:
    """Most recent value per metric_name for a server (time-series `Metric` rows)."""
    result = await db.execute(
        select(Metric.metric_name, Metric.metric_value, Metric.timestamp)
        .where(Metric.server_id == server_id)
        .order_by(Metric.timestamp.desc())
        .limit(500)
    )
    latest: Dict[str, float] = {}
    for name, value, _ts in result.all():
        if name not in latest:
            latest[name] = float(value or 0.0)
    return latest


def _metric_float(metrics: Dict[str, float], *names: str) -> float:
    for n in names:
        if n in metrics:
            return float(metrics[n])
    return 0.0


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

    health_overview: List[ServerHealthOverview] = []
    for server in servers:
        by_name = await _latest_metric_values(db, server.id)
        health_overview.append(
            ServerHealthOverview(
                server_id=server.id,
                server_name=server.hostname,
                status=server.status,
                cpu_usage=_metric_float(by_name, "cpu_usage", "cpu_percent"),
                memory_usage=_metric_float(by_name, "memory_usage", "memory_percent"),
                disk_usage=_metric_float(by_name, "disk_usage", "disk_usage_percent"),
                uptime=int(_metric_float(by_name, "uptime_seconds")),
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

    alerts_query = (
        select(Alert, Server.hostname)
        .outerjoin(Server, Alert.server_id == Server.id)
        .where(
            Alert.organization_id.in_(org_ids) if org_ids else False,
            Alert.status != "resolved",
        )
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    alerts_result = await db.execute(alerts_query)
    alerts = alerts_result.fetchall()

    recent_alerts: List[RecentAlert] = []
    for alert, hostname in alerts:
        label = (alert.type or "alert").replace("_", " ").title()
        recent_alerts.append(
            RecentAlert(
                id=alert.id,
                server_name=hostname or "Unknown server",
                severity=alert.type or "info",
                title=f"{label}",
                message=f"Value {alert.value} (threshold {alert.threshold}) — status {alert.status}",
                created_at=alert.created_at.isoformat(),
            )
        )

    return recent_alerts

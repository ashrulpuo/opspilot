"""Salt API endpoints for OpsPilot.
Handles incoming data from Salt runners (metrics, backups, health, logs).
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.metrics import Metric
from app.models.server import Server
from app.models.alert import Alert
from sqlalchemy import select, func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Request Schemas
# ============================================

class MetricsIngestionRequest(BaseModel):
    """Metrics ingestion request schema."""

    server_id: str
    organization_id: str
    metrics: Dict[str, Any]


class BackupReportRequest(BaseModel):
    """Backup report request schema."""

    server_id: str
    organization_id: str
    backup_results: Dict[str, Any]


class HealthReportRequest(BaseModel):
    """Health report request schema."""

    server_id: str
    organization_id: str
    checks: Dict[str, Any]


class LogShipmentRequest(BaseModel):
    """Log shipment request schema."""

    server_id: str
    logs: List[Dict[str, Any]]


# ============================================
# Response Schemas
# ============================================

class MetricsIngestionResponse(BaseModel):
    """Metrics ingestion response schema."""

    status: str
    message: str


class BackupReportResponse(BaseModel):
    """Backup report response schema."""

    status: str
    message: str


class HealthReportResponse(BaseModel):
    """Health report response schema."""

    status: str
    message: str


class LogShipmentResponse(BaseModel):
    """Log shipment response schema."""

    status: str
    message: str
    processed_count: int


# ============================================
# Endpoints
# ============================================

@router.post("/metrics", response_model=MetricsIngestionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_metrics(
    request: MetricsIngestionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Ingest metrics from Salt runner.

    Args:
        request: Metrics ingestion data
        db: Database session
        api_key: API key for authentication

    Returns:
        Ingestion confirmation

    Raises:
        HTTPException: If authentication fails or server not found
    """
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify server exists
    server_result = await db.execute(
        select(Server).where(Server.id == request.server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        logger.warning(f"Metrics ingestion failed: server {request.server_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # Extract metrics
    metrics_data = request.metrics
    metrics = Metrics(
        server_id=request.server_id,
        timestamp=datetime.utcnow(),
        cpu_usage_percent=metrics_data.get("cpu_percent", 0),
        cpu_count=metrics_data.get("cpu_count", 0),
        memory_usage_percent=metrics_data.get("memory_percent", 0),
        memory_used_gb=metrics_data.get("memory_used_gb", 0),
        memory_total_gb=metrics_data.get("memory_total_gb", 0),
        disk_usage_percent=metrics_data.get("disk_usage_percent", 0),
        disk_used_gb=metrics_data.get("disk_used_gb", 0),
        disk_total_gb=metrics_data.get("disk_total_gb", 0),
        network_in_bps=metrics_data.get("network_in_bps", 0),
        network_out_bps=metrics_data.get("network_out_bps", 0),
        uptime_seconds=metrics_data.get("uptime_seconds", 0),
    )

    db.add(metrics)

    # Update server last_seen and status
    server.last_seen = datetime.utcnow()
    server.status = "online"

    # Check for alerts based on thresholds
    await check_alert_thresholds(db, server, metrics_data)

    await db.commit()

    logger.info(f"Metrics ingested for server {request.server_id}")
    return MetricsIngestionResponse(
        status="success",
        message="Metrics ingested successfully",
    )


@router.post("/backups", response_model=BackupReportResponse, status_code=status.HTTP_201_CREATED)
async def report_backup(
    request: BackupReportRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Report backup execution from Salt runner.

    Args:
        request: Backup report data
        db: Database session
        api_key: API key for authentication

    Returns:
        Report confirmation

    Raises:
        HTTPException: If authentication fails or server not found
    """
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify server exists
    server_result = await db.execute(
        select(Server).where(Server.id == request.server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        logger.warning(f"Backup report failed: server {request.server_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # TODO: Store backup report in backups table
    backup_results = request.backup_results

    logger.info(f"Backup report received for server {request.server_id}: {backup_results}")
    return BackupReportResponse(
        status="success",
        message="Backup report received successfully",
    )


@router.post("/health", response_model=HealthReportResponse, status_code=status.HTTP_201_CREATED)
async def report_health(
    request: HealthReportRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Report health check results from Salt runner.

    Args:
        request: Health report data
        db: Database session
        api_key: API key for authentication

    Returns:
        Report confirmation

    Raises:
        HTTPException: If authentication fails or server not found
    """
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify server exists
    server_result = await db.execute(
        select(Server).where(Server.id == request.server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        logger.warning(f"Health report failed: server {request.server_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # TODO: Store health report in health_checks table
    health_checks = request.checks

    logger.info(f"Health report received for server {request.server_id}: {health_checks}")
    return HealthReportResponse(
        status="success",
        message="Health report received successfully",
    )


@router.post("/logs", response_model=LogShipmentResponse, status_code=status.HTTP_201_CREATED)
async def ship_logs(
    request: LogShipmentRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Ship logs from Salt runner.

    Args:
        request: Log shipment data
        db: Database session
        api_key: API key for authentication

    Returns:
        Shipment confirmation

    Raises:
        HTTPException: If authentication fails or server not found
    """
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Verify server exists
    server_result = await db.execute(
        select(Server).where(Server.id == request.server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        logger.warning(f"Log shipment failed: server {request.server_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # TODO: Store logs in logs table
    logs = request.logs
    processed_count = len(logs)

    logger.info(f"Logs shipped for server {request.server_id}: {processed_count} logs")
    return LogShipmentResponse(
        status="success",
        message=f"Logs shipped successfully",
        processed_count=processed_count,
    )


# ============================================
# Helper Functions
# ============================================

async def check_alert_thresholds(
    db: AsyncSession,
    server: Server,
    metrics_data: Dict[str, Any],
):
    """Check metrics against alert thresholds and create alerts if needed.

    Args:
        db: Database session
        server: Server instance
        metrics_data: Metrics data from runner
    """
    cpu_percent = metrics_data.get("cpu_percent", 0)
    memory_percent = metrics_data.get("memory_percent", 0)
    disk_percent = metrics_data.get("disk_usage_percent", 0)

    # Default thresholds (can be overridden by organization/server config)
    cpu_threshold = 90
    memory_threshold = 90
    disk_threshold = 85

    # Check CPU
    if cpu_percent > cpu_threshold:
        await create_alert(
            db,
            server=server,
            alert_type="cpu",
            severity="critical" if cpu_percent > 95 else "warning",
            title="High CPU Usage",
            message=f"CPU usage is {cpu_percent}%",
            value=cpu_percent,
            threshold=cpu_threshold,
        )

    # Check Memory
    if memory_percent > memory_threshold:
        await create_alert(
            db,
            server=server,
            alert_type="memory",
            severity="critical" if memory_percent > 95 else "warning",
            title="High Memory Usage",
            message=f"Memory usage is {memory_percent}%",
            value=memory_percent,
            threshold=memory_threshold,
        )

    # Check Disk
    if disk_percent > disk_threshold:
        await create_alert(
            db,
            server=server,
            alert_type="disk",
            severity="critical" if disk_percent > 95 else "warning",
            title="High Disk Usage",
            message=f"Disk usage is {disk_percent}%",
            value=disk_percent,
            threshold=disk_threshold,
        )


async def create_alert(
    db: AsyncSession,
    server: Server,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    value: Optional[float] = None,
    threshold: Optional[float] = None,
):
    """Create a new alert.

    Args:
        db: Database session
        server: Server instance
        alert_type: Alert type (cpu, memory, disk, etc.)
        severity: Alert severity (critical, warning, info)
        title: Alert title
        message: Alert message
        value: Alert value
        threshold: Alert threshold
    """
    import uuid

    alert = Alert(
        id=str(uuid.uuid4()),
        server_id=server.id,
        organization_id=server.organization_id,
        type=alert_type,
        severity=severity,
        title=title,
        message=message,
        value=value,
        threshold=threshold,
        resolved=False,
    )

    db.add(alert)
    logger.info(f"Alert created for server {server.id}: {title}")

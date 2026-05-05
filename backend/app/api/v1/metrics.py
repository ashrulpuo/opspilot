"""Metrics API endpoints for OpsPilot."""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from sqlalchemy import or_
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.agent_keys import verify_agent_api_key
from app.core.config import settings
from app.models.server import Server
from app.models.salt_event import SaltEvent
from app.models.notification import NotificationSmtpConfig, NotificationRecipient
from app.core.email import EmailService
from app.services.server_service import server_service
from app.services import metrics_push_service
from app.services.agent_push_service import apply_agent_push_payload

logger = logging.getLogger(__name__)

# (metric_keys, warning_threshold, critical_threshold, event_type)
_ALERT_THRESHOLDS = [
    (["cpu_percent", "cpu_usage"],              80.0, 95.0, "cpu_alert"),
    (["memory_percent", "memory_used_percent"], 85.0, 95.0, "memory_alert"),
    (["disk_usage_percent", "disk_usage"],      85.0, 95.0, "disk_alert"),
]
_ALERT_COOLDOWN_MINUTES = 5

_SSE_METRIC_FIELDS = [
    ("cpu_percent", "%"), ("cpu_usage", "%"),
    ("cpu_total_user", "%"), ("cpu_total_system", "%"),
    ("cpu_total_iowait", "%"), ("cpu_total_idle", "%"),
    ("memory_percent", "%"), ("memory_used_percent", "%"),
    ("disk_usage_percent", "%"), ("disk_usage", "%"),
    ("loadavg_1m", ""), ("loadavg_5m", ""), ("loadavg_15m", ""), ("uptime_seconds", "s"),
    ("process_count", ""), ("service_count", ""),
]

import re as _re
_CPU_CORE_PATTERN = _re.compile(r"^cpu_\d+_user$")


def _disk_metric_name(mountpoint: str) -> str:
    if mountpoint == "/":
        return "disk_usage__"
    slug = mountpoint.lstrip("/").replace("/", "_")
    return f"disk_usage_{slug}"


async def _publish_metrics_sse(server_id: str, metrics: Dict[str, Any]) -> None:
    """Publish metric events to Redis so SSE subscribers get realtime updates. Best-effort."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"metrics:{server_id}"
        now = datetime.utcnow().isoformat()

        async def _pub(key: str, val: Any, unit: str) -> None:
            try:
                await r.publish(channel, json.dumps({
                    "type": "metric", "event_type": "metric",
                    "server_id": server_id, "metric_name": key,
                    "metric_value": float(val), "unit": unit, "timestamp": now,
                }))
            except (TypeError, ValueError):
                pass

        for key, unit in _SSE_METRIC_FIELDS:
            val = metrics.get(key)
            if val is not None:
                await _pub(key, val, unit)

        # Dynamic per-core CPU fields: cpu_0_user, cpu_1_user, …
        for key, val in metrics.items():
            if _CPU_CORE_PATTERN.match(key) and val is not None:
                await _pub(key, val, "%")

        # Per-mount disk metrics with byte metadata
        disks = metrics.get("disks")
        if isinstance(disks, list):
            for disk in disks:
                if not isinstance(disk, dict):
                    continue
                mount = disk.get("mountpoint", "/")
                metric_name = _disk_metric_name(str(mount))
                used_pct = disk.get("used_percent", 0)
                try:
                    await r.publish(channel, json.dumps({
                        "type": "metric", "event_type": "metric",
                        "server_id": server_id, "metric_name": metric_name,
                        "metric_value": float(used_pct), "unit": "%",
                        "timestamp": now,
                        "metadata": {
                            "used_bytes": int(disk.get("used_bytes", 0)),
                            "total_bytes": int(disk.get("total_bytes", 0)),
                            "fstype": str(disk.get("fstype", "")),
                            "device": str(disk.get("device", "")),
                        },
                    }))
                except (TypeError, ValueError):
                    pass

        await r.aclose()
    except Exception as exc:
        logger.debug("SSE publish skipped: %s", exc)

async def _publish_processes_sse(server_id: str, processes: list) -> None:
    """Publish top-N process entries to Redis for SSE subscribers. Best-effort."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"processes:{server_id}"
        now = datetime.utcnow().isoformat()
        for proc in processes:
            pid = int(proc.get("pid", 0))
            await r.publish(channel, json.dumps({
                "type": "process_list",
                "server_id": server_id,
                "id": f"{server_id}_{pid}",
                "pid": pid,
                "name": str(proc.get("name", ""))[:80],
                "command": str(proc.get("command", ""))[:200],
                "username": str(proc.get("username", ""))[:32],
                "cpu_percent": float(proc.get("cpu_percent", 0)),
                "memory_percent": float(proc.get("memory_percent", 0)),
                "state": (str(proc.get("state", "S"))[:1] or "S"),
                "start_time": str(proc.get("start_time", now)),
                "timestamp": now,
            }))
        await r.aclose()
    except Exception as exc:
        logger.debug("SSE processes publish skipped: %s", exc)


async def _publish_services_sse(server_id: str, services: dict) -> None:
    """Publish service state entries to Redis for SSE subscribers. Best-effort."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"services:{server_id}"
        now = datetime.utcnow().isoformat()
        for svc_name, svc_val in services.items():
            if isinstance(svc_val, dict):
                status = svc_val.get("status", "stopped")
                sub_state = svc_val.get("sub_state", "")
                enabled = svc_val.get("enabled", "")
                description = svc_val.get("description", "")
            else:
                status = "running" if svc_val == "running" else "stopped"
                sub_state = ""
                enabled = ""
                description = ""
            await r.publish(channel, json.dumps({
                "type": "service_state",
                "server_id": server_id,
                "id": f"{server_id}_{svc_name}",
                "service_name": svc_name,
                "status": status,
                "sub_state": sub_state,
                "enabled": enabled,
                "description": description,
                "last_checked": now,
                "timestamp": now,
            }))
        await r.aclose()
    except Exception as exc:
        logger.debug("SSE services publish skipped: %s", exc)


async def _check_and_emit_alerts(
    db: AsyncSession, server_id: str, metrics: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Write SaltEvent rows for threshold breaches (with cooldown). Returns list for SSE publish."""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=_ALERT_COOLDOWN_MINUTES)
    to_publish: List[Dict[str, Any]] = []

    for keys, warn_pct, crit_pct, event_type in _ALERT_THRESHOLDS:
        val: Optional[float] = None
        for k in keys:
            v = metrics.get(k)
            if v is not None:
                try:
                    val = float(v)
                    break
                except (TypeError, ValueError):
                    continue
        if val is None:
            continue

        if val >= crit_pct:
            severity = "critical"
        elif val >= warn_pct:
            severity = "warning"
        else:
            continue

        # Cooldown: skip if same event_type fired within the window
        recent = await db.scalar(
            select(func.count()).select_from(SaltEvent).where(
                SaltEvent.server_id == server_id,
                SaltEvent.event_type == event_type,
                SaltEvent.created_at > cutoff,
            )
        )
        if recent:
            continue

        label = event_type.replace("_alert", "").upper()
        threshold = crit_pct if severity == "critical" else warn_pct
        msg = f"{label} usage at {val:.1f}% exceeds {severity} threshold ({threshold:.0f}%)"
        db.add(SaltEvent(
            server_id=server_id,
            event_tag=f"opspilot/{event_type}",
            event_type=event_type,
            event_data={"message": msg, "severity": severity, "value": val},
            processed=False,
            created_at=now,
        ))
        to_publish.append({
            "id": f"{server_id}_{event_type}_{now.isoformat()}",
            "event_type": event_type,
            "message": msg,
            "severity": severity,
            "created_at": now.isoformat() + 'Z',
        })

    return to_publish


async def _publish_alert_sse(server_id: str, alerts: List[Dict[str, Any]]) -> None:
    """Publish alert events to Redis for SSE subscribers. Best-effort."""
    if not alerts:
        return
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"alerts:{server_id}"
        for alert in alerts:
            await r.publish(channel, json.dumps({
                "type": "alert",
                "id": alert["id"],
                "server_id": server_id,
                "alert_type": alert["event_type"],
                "severity": alert["severity"],
                "message": alert["message"],
                "event_data": {},
                "processed": False,
                "created_at": alert["created_at"],
            }))
        await r.aclose()
    except Exception as exc:
        logger.debug("SSE alert publish skipped: %s", exc)


async def _send_alert_emails(
    db: AsyncSession,
    org_id: str,
    server_hostname: str,
    server_id: str,
    alerts: List[Dict[str, Any]],
) -> None:
    """Send email notifications for threshold-triggered alerts. Best-effort."""
    if not alerts:
        return
    try:
        smtp_result = await db.execute(
            select(NotificationSmtpConfig).where(
                NotificationSmtpConfig.organization_id == org_id,
                NotificationSmtpConfig.enabled == True,
            )
        )
        smtp_config = smtp_result.scalar_one_or_none()
        if not smtp_config:
            return

        for alert in alerts:
            severity = alert["severity"]
            severity_conditions = [
                NotificationRecipient.severity_filter == "all",
                NotificationRecipient.severity_filter == severity,
            ]
            if severity == "critical":
                severity_conditions.append(NotificationRecipient.severity_filter == "warning")

            recipients_result = await db.execute(
                select(NotificationRecipient).where(
                    NotificationRecipient.organization_id == org_id,
                    NotificationRecipient.enabled == True,
                    or_(*severity_conditions),
                )
            )
            to_emails = [r.email for r in recipients_result.scalars().all()]
            if not to_emails:
                continue

            try:
                svc = EmailService(
                    host=smtp_config.host,
                    port=smtp_config.port,
                    username=smtp_config.username,
                    password=smtp_config.password,
                    from_address=smtp_config.from_address or smtp_config.username,
                    use_tls=smtp_config.use_tls,
                )
                svc.send_alert_notification(
                    to_emails=to_emails,
                    alert_data={
                        "id": alert["id"],
                        "server_hostname": server_hostname,
                        "type": alert["event_type"].replace("_alert", ""),
                        "severity": severity,
                        "message": alert["message"],
                        "threshold": None,
                        "actual_value": None,
                        "triggered_at": alert["created_at"],
                    },
                )
                logger.info("Alert email sent for %s to %s", alert["event_type"], to_emails)
            except Exception as e:
                logger.error("Alert email failed for %s: %s", alert["event_type"], e)
    except Exception as e:
        logger.error("_send_alert_emails error: %s", e)


router = APIRouter()


# Request Schemas
class MetricsIngestRequest(BaseModel):
    """Agent push: metrics plus optional Salt snapshot sections (same X-API-Key)."""

    server_id: str
    organization_id: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    host_profile: Optional[Dict[str, Any]] = None
    processes: Optional[List[Dict[str, Any]]] = None
    services: Optional[Dict[str, Any]] = None
    packages: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    logs: Optional[List[Dict[str, Any]]] = None
    events: Optional[List[Dict[str, Any]]] = None


class MetricsIngestResponse(BaseModel):
    """Metrics ingestion response schema."""

    message: str
    server_id: str


# Response Schemas
class MetricsResponse(BaseModel):
    """Metrics response schema."""

    server_id: str
    metrics: Dict[str, Any]


@router.post("/servers/{server_id}/metrics", response_model=MetricsIngestResponse)
async def ingest_metrics(
    server_id: str,
    request: MetricsIngestRequest,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Ingest metrics from OpsPilot host agent (push). Requires per-server X-API-Key."""
    if server_id != request.server_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server ID in URL does not match request body",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    if not server.agent_api_key_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server has no agent API key registered",
        )

    if not verify_agent_api_key(x_api_key, server.agent_api_key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if server.organization_id != request.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id does not match this server",
        )

    # Require at least one payload section (metrics snapshot or optional sections).
    has_any = bool(request.metrics) or any(
        [
            request.host_profile,
            request.processes is not None,
            request.services is not None,
            request.packages is not None,
            request.logs is not None,
            request.events is not None,
        ]
    )
    if not has_any:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty payload: provide metrics and/or host_profile, processes, services, packages, logs, or events",
        )

    await apply_agent_push_payload(
        db,
        server,
        metrics=request.metrics or {},
        host_profile=request.host_profile,
        processes=request.processes,
        services=request.services,
        packages=request.packages,
        logs=request.logs,
        events=request.events,
    )
    await metrics_push_service.mark_agent_seen(db, server)

    pending_alerts: List[Dict[str, Any]] = []
    if request.metrics:
        pending_alerts = await _check_and_emit_alerts(db, server_id, request.metrics)

    await db.commit()

    if request.metrics:
        await _publish_metrics_sse(server_id, request.metrics)
    if pending_alerts:
        await _publish_alert_sse(server_id, pending_alerts)
        await _send_alert_emails(db, server.organization_id, server.hostname, server_id, pending_alerts)
    if request.processes:
        await _publish_processes_sse(server_id, request.processes)
    if request.services:
        await _publish_services_sse(server_id, request.services)

    return MetricsIngestResponse(
        message="Agent data received successfully",
        server_id=server_id,
    )


@router.get("/servers/{server_id}/metrics", response_model=MetricsResponse)
async def get_server_metrics(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get latest metrics for a server (prefers fresh push-agent samples, else Salt)."""
    user_id = current_user["id"]

    try:
        metrics = await server_service.get_metrics_for_dashboard(db, server_id, user_id)
        return MetricsResponse(server_id=server_id, metrics=metrics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/servers/{server_id}/metrics/history")
async def get_server_metrics_history(
    server_id: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get historical metrics for a server."""
    user_id = current_user["id"]

    try:
        server = await server_service.get_server(db, server_id, user_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this server",
        )

    return {
        "server_id": server_id,
        "hours": hours,
        "message": "Historical metrics retrieval not yet implemented",
    }


@router.get("/organizations/{organization_id}/metrics/summary")
async def get_organization_metrics_summary(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get metrics summary for all servers in an organization."""
    user_id = current_user["id"]

    return {
        "organization_id": organization_id,
        "message": "Metrics summary not yet implemented",
    }

"""JWT-authenticated reads for Salt snapshot data persisted from minion pushes."""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.salt_event import SaltEvent
from app.models.salt_minion import SaltMinion
from app.models.salt_package import SaltPackage
from app.models.salt_process import SaltProcess
from app.models.salt_service_state import SaltServiceState
from app.models.server import Server
from app.services.salt_service import salt_service
from app.services.server_service import server_service

router = APIRouter()


class ProcessOut(BaseModel):
    id: str
    server_id: str
    pid: int
    name: str
    command: Optional[str] = None
    username: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    state: str
    start_time: Optional[str] = None


class ProcessKillResponse(BaseModel):
    status: str
    pid: int
    signal: int
    result: Any = None


class ServiceStateOut(BaseModel):
    id: str
    server_id: str
    service_name: str
    status: str
    previous_status: Optional[str] = None
    sub_state: Optional[str] = None
    status_changed_at: Optional[str] = None
    enabled: Optional[str] = None
    description: Optional[str] = None
    last_checked: str


class PackageOut(BaseModel):
    name: str
    version: str


class SaltLogOut(BaseModel):
    id: str
    timestamp: str
    log_level: str
    source: str
    message: str
    extra: Optional[dict] = None


class LogStatsOut(BaseModel):
    total: int
    info: int
    warn: int
    error: int
    debug: int


class LogsPagedOut(BaseModel):
    items: List[SaltLogOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    stats: LogStatsOut


class SaltEventOut(BaseModel):
    alert_type: str
    message: str
    severity: str
    created_at: str


class OverviewQuickStats(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    service_count: int
    process_count: int


class ServerOverviewResponse(BaseModel):
    quick_stats: OverviewQuickStats
    recent_alerts: List[SaltEventOut]


class NetworkInterface(BaseModel):
    iface: str
    mac: str = ""
    ipv4: str = ""
    ipv4_prefix: str = ""
    ipv6: str = ""
    ipv6_prefix: str = ""
    is_up: bool = True


class HostInfoResponse(BaseModel):
    server_id: str
    hostname: Optional[str] = None
    fqdn: Optional[str] = None
    ip_address: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    architecture: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_model: Optional[str] = None
    memory_mb: Optional[int] = None
    kernel: Optional[str] = None
    timezone: Optional[str] = None
    virtual: Optional[bool] = None
    virtual_type: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    cloud_instance_type: Optional[str] = None
    network_interfaces: List[NetworkInterface] = []
    last_seen_at: Optional[str] = None
    facts_synced_at: Optional[str] = None


@router.get("/servers/{server_id}/host-info", response_model=HostInfoResponse)
async def get_server_host_info(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Return extended host profile collected by the push agent."""
    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    hi = server.host_info or {}
    raw_ifaces = hi.get("network_interfaces") or []
    ifaces = []
    for iface in raw_ifaces:
        if not isinstance(iface, dict):
            continue
        ifaces.append(NetworkInterface(
            iface=str(iface.get("iface", "")),
            mac=str(iface.get("mac", "")),
            ipv4=str(iface.get("ipv4", "")),
            ipv4_prefix=str(iface.get("ipv4_prefix", "")),
            ipv6=str(iface.get("ipv6", "")),
            ipv6_prefix=str(iface.get("ipv6_prefix", "")),
            is_up=bool(iface.get("is_up", True)),
        ))

    return HostInfoResponse(
        server_id=server_id,
        hostname=server.agent_reported_hostname,
        fqdn=hi.get("fqdn"),
        ip_address=server.agent_reported_ip,
        os_name=server.agent_os_name,
        os_version=server.agent_os_version,
        architecture=server.agent_architecture,
        cpu_cores=server.agent_cpu_cores,
        cpu_model=hi.get("cpu_model"),
        memory_mb=server.agent_memory_mb,
        kernel=hi.get("kernel"),
        timezone=hi.get("timezone"),
        virtual=hi.get("virtual"),
        virtual_type=hi.get("virtual_type"),
        cloud_provider=hi.get("cloud_provider"),
        cloud_region=hi.get("cloud_region"),
        cloud_instance_type=hi.get("cloud_instance_type"),
        network_interfaces=ifaces,
        last_seen_at=server.agent_last_seen_at.isoformat() + 'Z' if server.agent_last_seen_at else None,
        facts_synced_at=server.agent_facts_synced_at.isoformat() + 'Z' if server.agent_facts_synced_at else None,
    )


def _metric_float(raw: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for k in keys:
        if k in raw and raw[k] is not None:
            try:
                return float(raw[k])
            except (TypeError, ValueError):
                continue
    return default


@router.get("/servers/{server_id}/salt/processes", response_model=List[ProcessOut])
async def list_salt_processes(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    result = await db.execute(
        select(SaltProcess).where(SaltProcess.server_id == server_id).order_by(SaltProcess.cpu_percent.desc()).limit(500)
    )
    rows = result.scalars().all()
    return [
        ProcessOut(
            id=r.id,
            server_id=r.server_id,
            pid=r.pid,
            name=r.name,
            command=r.command,
            username=r.username,
            cpu_percent=r.cpu_percent,
            memory_percent=r.memory_percent,
            memory_mb=r.memory_mb,
            state=r.state,
            start_time=r.start_time.isoformat() + 'Z' if r.start_time else None,
        )
        for r in rows
    ]


@router.get("/servers/{server_id}/salt/services", response_model=List[ServiceStateOut])
async def list_salt_services(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    result = await db.execute(select(SaltServiceState).where(SaltServiceState.server_id == server_id))
    rows = result.scalars().all()
    return [
        ServiceStateOut(
            id=r.id,
            server_id=r.server_id,
            service_name=r.service_name,
            status=r.status,
            previous_status=r.previous_status,
            sub_state=r.sub_state,
            enabled=r.enabled,
            description=r.description,
            last_checked=r.last_checked.isoformat() + 'Z',
            status_changed_at=(sc := getattr(r, 'status_changed_at', None)) and sc.isoformat() + 'Z' or None,
        )
        for r in rows
    ]


@router.get("/servers/{server_id}/salt/packages", response_model=List[PackageOut])
async def list_salt_packages(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(500, ge=1, le=5000),
):
    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    result = await db.execute(select(SaltPackage).where(SaltPackage.server_id == server_id).limit(limit))
    rows = result.scalars().all()
    return [PackageOut(name=r.name, version=r.version) for r in rows]


@router.get("/servers/{server_id}/salt/logs", response_model=LogsPagedOut)
async def list_salt_logs(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    from app.models.salt_log import SaltLog

    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    base_where = [SaltLog.server_id == server_id]
    if level:
        base_where.append(SaltLog.log_level == level.upper())
    if source:
        base_where.append(SaltLog.source == source)
    if search:
        base_where.append(SaltLog.message.ilike(f"%{search}%"))

    # stats across full filtered set (not just current page)
    stats_result = await db.execute(
        select(SaltLog.log_level, func.count().label("cnt"))
        .where(*base_where)
        .group_by(SaltLog.log_level)
    )
    counts: dict[str, int] = {row.log_level: row.cnt for row in stats_result}
    total = sum(counts.values())
    stats = LogStatsOut(
        total=total,
        info=counts.get("INFO", 0),
        warn=counts.get("WARN", 0),
        error=counts.get("ERROR", 0),
        debug=counts.get("DEBUG", 0),
    )

    offset = (page - 1) * page_size
    rows_result = await db.execute(
        select(SaltLog)
        .where(*base_where)
        .order_by(SaltLog.timestamp.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = rows_result.scalars().all()
    import math
    total_pages = max(1, math.ceil(total / page_size))

    return LogsPagedOut(
        items=[
            SaltLogOut(
                id=r.id,
                timestamp=r.timestamp.isoformat() + "Z",
                log_level=r.log_level,
                source=r.source,
                message=r.message[:4000],
                extra=r.extra,
            )
            for r in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        stats=stats,
    )


class SourceStatOut(BaseModel):
    source: str
    count: int


@router.get("/servers/{server_id}/salt/logs/source-stats", response_model=List[SourceStatOut])
async def list_salt_log_source_stats(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    from app.models.salt_log import SaltLog

    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    result = await db.execute(
        select(SaltLog.source, func.count().label("cnt"))
        .where(SaltLog.server_id == server_id)
        .group_by(SaltLog.source)
        .order_by(func.count().desc())
    )
    return [SourceStatOut(source=row.source, count=row.cnt) for row in result]


@router.get("/servers/{server_id}/salt/logs/sources", response_model=List[str])
async def list_salt_log_sources(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    from app.models.salt_log import SaltLog
    from sqlalchemy import distinct

    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    result = await db.execute(
        select(distinct(SaltLog.source))
        .where(SaltLog.server_id == server_id)
        .order_by(SaltLog.source)
    )
    return [row[0] for row in result]


@router.get("/servers/{server_id}/overview-panel", response_model=ServerOverviewResponse)
async def get_server_overview_panel(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Quick stats + recent alerts for Server Overview (tabs use dedicated list endpoints)."""
    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    raw = await server_service.get_metrics_for_dashboard(db, server_id, user_id)

    cpu = _metric_float(raw, "cpu_percent", "cpu_usage", default=0.0)
    if cpu == 0.0:
        cpu = min(100.0, _metric_float(raw, "loadavg_1m", default=0.0) * 25.0)
    mem = _metric_float(raw, "memory_percent", "memory_used_percent", default=0.0)
    disk = _metric_float(raw, "disk_usage_percent", "disk_usage", default=0.0)

    svc_n = await db.scalar(
        select(func.count()).select_from(SaltServiceState).where(SaltServiceState.server_id == server_id)
    )
    proc_n = await db.scalar(
        select(func.count()).select_from(SaltProcess).where(SaltProcess.server_id == server_id)
    )

    ev_result = await db.execute(
        select(SaltEvent)
        .where(SaltEvent.server_id == server_id)
        .order_by(SaltEvent.created_at.desc())
        .limit(5)
    )
    events = ev_result.scalars().all()
    alerts: List[SaltEventOut] = []
    for e in events:
        data = e.event_data if isinstance(e.event_data, dict) else {}
        msg = data.get("message") or data.get("detail") or str(data)[:500]
        sev = str(data.get("severity") or "info").lower()
        if sev not in ("critical", "warning", "info"):
            sev = "info"
        alerts.append(
            SaltEventOut(
                alert_type=e.event_type,
                message=str(msg)[:2000],
                severity=sev,
                created_at=e.created_at.isoformat() + 'Z',
            )
        )

    return ServerOverviewResponse(
        quick_stats=OverviewQuickStats(
            cpu_percent=round(cpu, 1),
            memory_percent=round(mem, 1),
            disk_percent=round(disk, 1),
            service_count=int(svc_n or 0),
            process_count=int(proc_n or 0),
        ),
        recent_alerts=alerts,
    )


class ServiceControlResponse(BaseModel):
    status: str
    action: str
    service_name: str
    result: Optional[Any] = None


@router.post("/servers/{server_id}/services/{service_name}/control", response_model=ServiceControlResponse)
async def control_service(
    server_id: str,
    service_name: str,
    action: Literal["start", "stop", "restart"],
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Start, stop, or restart a systemd service on the target server via Salt."""
    user_id = current_user["id"]
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    minion_result = await db.execute(select(SaltMinion).where(SaltMinion.server_id == server_id))
    minion = minion_result.scalar_one_or_none()
    if not minion:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Salt minion registered for this server")

    try:
        salt_result = await salt_service._execute(
            "local", minion.minion_id, f"service.{action}", args=[service_name]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Salt command failed: {e}")

    return ServiceControlResponse(status="ok", action=action, service_name=service_name, result=salt_result)

"""Monitors API — uptime, SSL, TCP, DNS, push heartbeat checks."""
import asyncio
import logging
import secrets
import socket
import ssl
import time
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.core.security import get_current_user
from app.core.email import EmailService
from app.models.monitor import Monitor, MonitorCheck, MonitorIncident
from app.models.notification import NotificationSmtpConfig, NotificationRecipient
from app.models.organization import OrganizationMember

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class MonitorCreate(BaseModel):
    name: str
    url: str = ""
    type: str = "https"
    port: Optional[int] = None
    interval_seconds: int = 300
    timeout_seconds: int = 10
    dns_resolve_type: Optional[str] = None
    dns_resolve_expected: Optional[str] = None


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    port: Optional[int] = None
    interval_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    enabled: Optional[bool] = None
    dns_resolve_type: Optional[str] = None
    dns_resolve_expected: Optional[str] = None


class MonitorResponse(BaseModel):
    id: str
    org_id: str
    server_id: Optional[str]
    name: str
    url: str
    type: str
    port: Optional[int]
    interval_seconds: int
    timeout_seconds: int
    enabled: bool
    last_status: Optional[str]
    last_checked_at: Optional[datetime]
    consecutive_failures: int
    heartbeat_api_key: Optional[str]
    ssl_days_remaining: Optional[float]
    avg_response_time_ms: Optional[float]
    uptime_7d: Optional[float]
    uptime_30d: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_obj(cls, m: Monitor) -> "MonitorResponse":
        return cls(
            id=m.id,
            org_id=m.organization_id,
            server_id=m.server_id,
            name=m.name,
            url=m.url,
            type=m.type,
            port=m.port,
            interval_seconds=m.interval_seconds,
            timeout_seconds=m.timeout_seconds,
            enabled=m.enabled,
            last_status=m.last_status,
            last_checked_at=m.last_checked_at,
            consecutive_failures=m.consecutive_failures,
            heartbeat_api_key=m.heartbeat_api_key,
            ssl_days_remaining=m.ssl_days_remaining,
            avg_response_time_ms=m.avg_response_time_ms,
            uptime_7d=m.uptime_7d,
            uptime_30d=m.uptime_30d,
            created_at=m.created_at,
        )


class MonitorCheckResponse(BaseModel):
    id: str
    monitor_id: str
    checked_at: datetime
    status: str
    response_time_ms: Optional[float]
    status_code: Optional[int]
    ssl_days_remaining: Optional[float]
    error: Optional[str]

    class Config:
        from_attributes = True


class MonitorIncidentResponse(BaseModel):
    id: str
    monitor_id: str
    started_at: datetime
    resolved_at: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


class MonitorStatsResponse(BaseModel):
    total: int
    up: int
    down: int
    paused: int
    pending: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


async def _org_id_for_user(user, db: AsyncSession) -> str:
    r = await db.execute(
        select(OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == user.id)
        .limit(1)
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=403, detail="No organization")
    return row


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/monitors/stats", response_model=MonitorStatsResponse, tags=["Monitors"])
async def get_monitor_stats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    r = await db.execute(select(Monitor).where(Monitor.organization_id == org_id))
    monitors = r.scalars().all()
    total = len(monitors)
    up = paused = down = pending = 0
    for m in monitors:
        if not m.enabled:
            paused += 1
        elif m.last_status == "up":
            up += 1
        elif m.last_status == "down":
            down += 1
        else:
            pending += 1
    return MonitorStatsResponse(total=total, up=up, down=down, paused=paused, pending=pending)


@router.get("/monitors", response_model=List[MonitorResponse], tags=["Monitors"])
async def list_monitors(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    r = await db.execute(
        select(Monitor)
        .where(Monitor.organization_id == org_id)
        .order_by(Monitor.created_at.desc())
    )
    return [MonitorResponse.from_orm_obj(m) for m in r.scalars().all()]


@router.post("/monitors", response_model=MonitorResponse, status_code=201, tags=["Monitors"])
async def create_monitor(
    data: MonitorCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    now = datetime.utcnow()
    m = Monitor(
        id=_new_id(),
        organization_id=org_id,
        name=data.name,
        url=data.url,
        type=data.type,
        port=data.port,
        interval_seconds=data.interval_seconds,
        timeout_seconds=data.timeout_seconds,
        dns_resolve_type=data.dns_resolve_type,
        dns_resolve_expected=data.dns_resolve_expected,
        enabled=True,
        consecutive_failures=0,
        heartbeat_api_key=secrets.token_urlsafe(32) if data.type == "push" else None,
        created_at=now,
        updated_at=now,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return MonitorResponse.from_orm_obj(m)


@router.get("/monitors/{monitor_id}", response_model=MonitorResponse, tags=["Monitors"])
async def get_monitor(
    monitor_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    m = await _get_monitor_or_404(monitor_id, org_id, db)
    return MonitorResponse.from_orm_obj(m)


@router.put("/monitors/{monitor_id}", response_model=MonitorResponse, tags=["Monitors"])
async def update_monitor(
    monitor_id: str,
    data: MonitorUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    m = await _get_monitor_or_404(monitor_id, org_id, db)
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(m, field, val)
    m.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(m)
    return MonitorResponse.from_orm_obj(m)


@router.delete("/monitors/{monitor_id}", status_code=204, tags=["Monitors"])
async def delete_monitor(
    monitor_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    m = await _get_monitor_or_404(monitor_id, org_id, db)
    await db.delete(m)
    await db.commit()


@router.get("/monitors/{monitor_id}/checks", response_model=List[MonitorCheckResponse], tags=["Monitors"])
async def get_monitor_checks(
    monitor_id: str,
    hours: int = 24,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    await _get_monitor_or_404(monitor_id, org_id, db)
    since = datetime.utcnow() - timedelta(hours=hours)
    r = await db.execute(
        select(MonitorCheck)
        .where(and_(MonitorCheck.monitor_id == monitor_id, MonitorCheck.checked_at >= since))
        .order_by(MonitorCheck.checked_at.desc())
        .limit(500)
    )
    return r.scalars().all()


@router.get("/monitors/{monitor_id}/incidents", response_model=List[MonitorIncidentResponse], tags=["Monitors"])
async def get_monitor_incidents(
    monitor_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = await _org_id_for_user(user, db)
    await _get_monitor_or_404(monitor_id, org_id, db)
    r = await db.execute(
        select(MonitorIncident)
        .where(MonitorIncident.monitor_id == monitor_id)
        .order_by(MonitorIncident.started_at.desc())
        .limit(100)
    )
    return r.scalars().all()


@router.post("/monitors/heartbeat/{api_key}", status_code=200, tags=["Monitors"])
async def receive_heartbeat(api_key: str, db: AsyncSession = Depends(get_db)):
    """Push monitor heartbeat — no auth, called by external service."""
    r = await db.execute(select(Monitor).where(Monitor.heartbeat_api_key == api_key))
    m = r.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Monitor not found")
    prev_status = m.last_status
    m.last_status = "up"
    m.last_checked_at = datetime.utcnow()
    m.consecutive_failures = 0
    m.updated_at = datetime.utcnow()
    await db.commit()
    if prev_status == "down":
        asyncio.create_task(_send_recovery_email(m.id, m.name, m.organization_id))
    return {"ok": True}


async def _get_monitor_or_404(monitor_id: str, org_id: str, db: AsyncSession) -> Monitor:
    r = await db.execute(
        select(Monitor).where(
            and_(Monitor.id == monitor_id, Monitor.organization_id == org_id)
        )
    )
    m = r.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return m


# ── Check engine ──────────────────────────────────────────────────────────────

class CheckResult:
    def __init__(self, status: str, response_time_ms: Optional[float] = None,
                 status_code: Optional[int] = None, ssl_days: Optional[float] = None,
                 error: Optional[str] = None):
        self.status = status
        self.response_time_ms = response_time_ms
        self.status_code = status_code
        self.ssl_days = ssl_days
        self.error = error


async def _check_http(monitor: Monitor) -> CheckResult:
    url = monitor.url
    if not url.startswith(("http://", "https://")):
        url = f"{'https' if monitor.type == 'https' else 'http'}://{url}"
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=monitor.timeout_seconds, follow_redirects=True,
                                     verify=(monitor.type == "https")) as client:
            resp = await client.get(url)
        elapsed = (time.monotonic() - t0) * 1000
        ok = resp.status_code < 400
        ssl_days = None
        if monitor.type == "https":
            ssl_days = await _get_ssl_days(url)
        return CheckResult(
            status="up" if ok else "down",
            response_time_ms=round(elapsed, 2),
            status_code=resp.status_code,
            ssl_days=ssl_days,
            error=None if ok else f"HTTP {resp.status_code}",
        )
    except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        return CheckResult(status="down", response_time_ms=round(elapsed, 2), error=str(e)[:200])


async def _check_tcp(monitor: Monitor) -> CheckResult:
    host = monitor.url or ""
    port = monitor.port or 80
    t0 = time.monotonic()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=monitor.timeout_seconds,
        )
        elapsed = (time.monotonic() - t0) * 1000
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return CheckResult(status="up", response_time_ms=round(elapsed, 2))
    except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        return CheckResult(status="down", response_time_ms=round(elapsed, 2), error=str(e)[:200])


async def _check_dns(monitor: Monitor) -> CheckResult:
    host = monitor.url or ""
    record_type = monitor.dns_resolve_type or "A"
    t0 = time.monotonic()
    try:
        loop = asyncio.get_event_loop()
        results = await asyncio.wait_for(
            loop.run_in_executor(None, socket.getaddrinfo, host, None),
            timeout=monitor.timeout_seconds,
        )
        elapsed = (time.monotonic() - t0) * 1000
        resolved = [str(r[4][0]) for r in results]
        expected = monitor.dns_resolve_expected
        if expected and expected not in resolved:
            return CheckResult(
                status="down",
                response_time_ms=round(elapsed, 2),
                error=f"Expected {expected}, got {resolved}",
            )
        return CheckResult(status="up", response_time_ms=round(elapsed, 2))
    except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        return CheckResult(status="down", response_time_ms=round(elapsed, 2), error=str(e)[:200])


async def _get_ssl_days(url: str) -> Optional[float]:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 443
        ctx = ssl.create_default_context()
        loop = asyncio.get_event_loop()

        def _get_cert():
            with ctx.wrap_socket(socket.create_connection((host, port), timeout=5), server_hostname=host) as s:
                return s.getpeercert()

        cert = await loop.run_in_executor(None, _get_cert)
        if cert and "notAfter" in cert:
            import ssl as _ssl
            expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            return max(0.0, (expiry - datetime.utcnow()).total_seconds() / 86400)
    except Exception:
        pass
    return None


async def _run_check(monitor: Monitor) -> CheckResult:
    if monitor.type in ("http", "https"):
        return await _check_http(monitor)
    elif monitor.type == "tcp":
        return await _check_tcp(monitor)
    elif monitor.type == "dns":
        return await _check_dns(monitor)
    return CheckResult(status="up")  # push: no active check


async def _persist_check(monitor_id: str, result: CheckResult, prev_status: Optional[str]) -> None:
    """Write check record, update monitor stats, open/close incidents, send email."""
    async with AsyncSessionLocal() as db:
        try:
            r = await db.execute(select(Monitor).where(Monitor.id == monitor_id))
            m = r.scalar_one_or_none()
            if not m:
                return

            now = datetime.utcnow()
            check = MonitorCheck(
                id=_new_id(),
                monitor_id=monitor_id,
                checked_at=now,
                status=result.status,
                response_time_ms=result.response_time_ms,
                status_code=result.status_code,
                ssl_days_remaining=result.ssl_days,
                error=result.error,
            )
            db.add(check)

            m.last_checked_at = now
            m.updated_at = now
            if result.ssl_days is not None:
                m.ssl_days_remaining = result.ssl_days

            notify_down = False
            notify_recovery = False

            if result.status == "up":
                was_down = m.last_status == "down"
                m.last_status = "up"
                m.consecutive_failures = 0
                if was_down:
                    notify_recovery = True
            else:
                # PRD: flip to DOWN only after 2 consecutive failures
                m.consecutive_failures = (m.consecutive_failures or 0) + 1
                if m.consecutive_failures >= 2:
                    was_not_down = m.last_status != "down"
                    m.last_status = "down"
                    if was_not_down:
                        notify_down = True

            status_changed = m.last_status != prev_status

            # Incident tracking
            if notify_down:
                incident = MonitorIncident(
                    id=_new_id(),
                    monitor_id=monitor_id,
                    started_at=now,
                )
                db.add(incident)
            elif notify_recovery:
                r2 = await db.execute(
                    select(MonitorIncident)
                    .where(and_(
                        MonitorIncident.monitor_id == monitor_id,
                        MonitorIncident.resolved_at.is_(None),
                    ))
                    .order_by(MonitorIncident.started_at.desc())
                    .limit(1)
                )
                open_incident = r2.scalar_one_or_none()
                if open_incident:
                    open_incident.resolved_at = now
                    open_incident.duration_seconds = int((now - open_incident.started_at).total_seconds())

            # Rolling uptime
            await _update_uptime(m, db)

            await db.commit()

            # Email notifications (after commit, uses explicit flags not status_changed)
            if notify_down:
                asyncio.create_task(_send_down_email(monitor_id, m.name, m.organization_id, result.error))
            elif notify_recovery:
                asyncio.create_task(_send_recovery_email(monitor_id, m.name, m.organization_id))

        except Exception:
            logger.exception("Error persisting check for monitor %s", monitor_id)


async def _update_uptime(m: Monitor, db: AsyncSession) -> None:
    """Compute uptime_7d and uptime_30d from recent checks."""
    for days, attr in ((7, "uptime_7d"), (30, "uptime_30d")):
        since = datetime.utcnow() - timedelta(days=days)
        r = await db.execute(
            select(
                func.count(MonitorCheck.id).label("total"),
                func.sum(func.cast(MonitorCheck.status == "up", type_=None)).label("up_count"),
            ).where(and_(MonitorCheck.monitor_id == m.id, MonitorCheck.checked_at >= since))
        )
        row = r.one_or_none()
        if row and row.total and row.total > 0:
            setattr(m, attr, round((row.up_count or 0) / row.total * 100, 2))


# ── Email helpers ─────────────────────────────────────────────────────────────

async def _get_email_service_and_recipients(org_id: str):
    """Return (EmailService, [emails]) or (None, []) if SMTP not configured."""
    async with AsyncSessionLocal() as db:
        r = await db.execute(
            select(NotificationSmtpConfig).where(
                and_(
                    NotificationSmtpConfig.organization_id == org_id,
                    NotificationSmtpConfig.enabled.is_(True),
                )
            )
        )
        smtp = r.scalar_one_or_none()
        if not smtp:
            return None, []
        r2 = await db.execute(
            select(NotificationRecipient).where(
                and_(
                    NotificationRecipient.organization_id == org_id,
                    NotificationRecipient.enabled.is_(True),
                )
            )
        )
        recipients = [rec.email for rec in r2.scalars().all()]
        svc = EmailService(
            host=smtp.host,
            port=smtp.port,
            username=smtp.username,
            password=smtp.password,
            from_address=smtp.from_address,
            use_tls=smtp.use_tls,
        )
        return svc, recipients


async def _send_down_email(monitor_id: str, name: str, org_id: str, error: Optional[str]) -> None:
    try:
        svc, recipients = await _get_email_service_and_recipients(org_id)
        if not svc or not recipients:
            return
        html = f"""
        <h2 style="color:#e53e3e">🔴 Monitor Down: {name}</h2>
        <p>Your monitor <strong>{name}</strong> is currently <strong>DOWN</strong>.</p>
        {f'<p><strong>Error:</strong> {error}</p>' if error else ''}
        <p style="color:#666;font-size:12px">OpsPilot Monitor</p>
        """
        svc.send_email(recipients, f"[DOWN] {name} is unreachable", html)
    except Exception:
        logger.exception("Failed to send down email for monitor %s", monitor_id)


async def _send_recovery_email(monitor_id: str, name: str, org_id: str) -> None:
    try:
        svc, recipients = await _get_email_service_and_recipients(org_id)
        if not svc or not recipients:
            return
        html = f"""
        <h2 style="color:#38a169">✅ Monitor Recovered: {name}</h2>
        <p>Your monitor <strong>{name}</strong> is back <strong>UP</strong>.</p>
        <p style="color:#666;font-size:12px">OpsPilot Monitor</p>
        """
        svc.send_email(recipients, f"[RECOVERED] {name} is back up", html)
    except Exception:
        logger.exception("Failed to send recovery email for monitor %s", monitor_id)


# ── Background checker loop ───────────────────────────────────────────────────

_checker_running = False


async def _checker_loop() -> None:
    global _checker_running
    _checker_running = True
    logger.info("Monitor checker started")
    while True:
        try:
            await _run_due_checks()
        except Exception:
            logger.exception("Monitor checker error")
        await asyncio.sleep(30)


async def _run_due_checks() -> None:
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Monitor).where(Monitor.enabled.is_(True)))
        monitors = r.scalars().all()

    now = datetime.utcnow()
    due = [
        m for m in monitors
        if m.type != "push" and (
            m.last_checked_at is None or
            (now - m.last_checked_at).total_seconds() >= m.interval_seconds
        )
    ]

    if not due:
        return

    async def _check_one(m: Monitor):
        prev = m.last_status
        result = await _run_check(m)
        await _persist_check(m.id, result, prev)

    await asyncio.gather(*[_check_one(m) for m in due], return_exceptions=True)


def start_monitor_checker() -> None:
    """Call from app startup to launch the background checker."""
    asyncio.create_task(_checker_loop())

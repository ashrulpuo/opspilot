"""Apply full minion push payload (metrics + host profile + optional salt tables) with per-server X-API-Key auth."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salt_log import SaltLog
from app.models.salt_package import SaltPackage
from app.models.salt_process import SaltProcess
from app.models.salt_service_state import SaltServiceState
from app.models.salt_event import SaltEvent
from app.models.server import Server
from app.services import metrics_push_service

logger = logging.getLogger(__name__)

ServiceStatus = str  # running|stopped|unknown


def _norm_service_status(raw: str) -> ServiceStatus:
    s = (raw or "").lower().strip()
    if s in ("running", "active", "true", "1", "on"):
        return "running"
    if s == "failed":
        return "failed"
    if s in ("stopped", "inactive", "false", "0", "disabled", "off", "dead", "exited"):
        return "stopped"
    return "unknown"


def _norm_proc_state(raw: str) -> str:
    s = (str(raw) or "S")[:1].upper()
    if s in ("R", "S", "D", "Z", "T", "W"):
        return s
    return "S"


def normalize_packages_data(
    raw: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]],
) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        out: Dict[str, Any] = {}
        for row in raw:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            if not name:
                continue
            out[str(name)] = {k: v for k, v in row.items() if k != "name"}
        return out
    return {}


def _apply_host_profile(server: Server, profile: Dict[str, Any], now: datetime) -> None:
    if not profile:
        return
    h = profile.get("hostname")
    if h:
        server.agent_reported_hostname = str(h)[:500]
    ips = profile.get("ips")
    if isinstance(ips, list) and ips:
        server.agent_reported_ip = str(ips[0])[:200]
    elif profile.get("ip_address"):
        server.agent_reported_ip = str(profile.get("ip_address"))[:200]
    if profile.get("os_name") is not None:
        server.agent_os_name = str(profile.get("os_name"))[:200]
    if profile.get("os_version") is not None:
        server.agent_os_version = str(profile.get("os_version"))[:200]
    if profile.get("architecture"):
        server.agent_architecture = str(profile.get("architecture"))[:128]
    nc = profile.get("cpu_cores") or profile.get("num_cpus")
    if nc is not None:
        try:
            server.agent_cpu_cores = int(nc)
        except (TypeError, ValueError):
            pass
    mem_mb = profile.get("memory_mb")
    if mem_mb is None and profile.get("memory_total_bytes") is not None:
        try:
            mem_mb = int(float(profile["memory_total_bytes"]) / (1024 * 1024))
        except (TypeError, ValueError):
            mem_mb = None
    if mem_mb is not None:
        try:
            server.agent_memory_mb = int(mem_mb)
        except (TypeError, ValueError):
            pass
    pretty = profile.get("os_pretty") or profile.get("os_full")
    if isinstance(pretty, str) and pretty.strip() and not server.agent_os_name:
        parts = pretty.split(None, 1)
        server.agent_os_name = parts[0][:200]
        if len(parts) > 1:
            server.agent_os_version = parts[1][:200]
    server.agent_facts_synced_at = now

    _EXTENDED_KEYS = (
        "kernel", "fqdn", "domain", "timezone", "cpu_model",
        "virtual", "virtual_type",
        "cloud_provider", "cloud_region", "cloud_instance_type",
        "network_interfaces",
    )
    extended = {k: profile[k] for k in _EXTENDED_KEYS if k in profile}
    if extended:
        existing = server.host_info or {}
        server.host_info = {**existing, **extended}


async def _sync_processes(db: AsyncSession, server_id: str, rows: List[Dict[str, Any]]) -> None:
    await db.execute(delete(SaltProcess).where(SaltProcess.server_id == server_id))
    now = datetime.utcnow()
    for proc in rows[:800]:
        if not isinstance(proc, dict):
            continue
        pid = proc.get("pid")
        try:
            pid_int = int(pid)
        except (TypeError, ValueError):
            continue
        sid = f"proc_{server_id}_{pid_int}"
        row = SaltProcess(
            id=sid,
            server_id=server_id,
            pid=pid_int,
            name=str(proc.get("name") or "?")[:500],
            command=str(proc.get("cmd") or proc.get("command") or "")[:8000] or None,
            username=str(proc.get("user") or proc.get("username") or "")[:200] or None,
            cpu_percent=float(proc.get("cpu_percent") or 0),
            memory_percent=float(proc.get("mem_percent") or proc.get("memory_percent") or 0),
            state=_norm_proc_state(str(proc.get("state") or "S")),
            start_time=now,
        )
        db.add(row)


async def _sync_packages(db: AsyncSession, server_id: str, pkgs: Dict[str, Any]) -> None:
    await db.execute(delete(SaltPackage).where(SaltPackage.server_id == server_id))
    now = datetime.utcnow()
    for pkg_name, info in list(pkgs.items())[:8000]:
        if not isinstance(pkg_name, str):
            continue
        if isinstance(info, str):
            ver = info
            meta: Dict[str, Any] = {}
        elif isinstance(info, dict):
            ver = str(info.get("version") or "")[:500]
            meta = info
        else:
            continue
        pid = f"pkg_{server_id}_{pkg_name}"[:180]
        db.add(
            SaltPackage(
                id=pid,
                server_id=server_id,
                name=pkg_name[:300],
                version=ver or "?",
                architecture=str(meta.get("arch") or meta.get("architecture") or "")[:64] or None,
                source=str(meta.get("source") or "unknown")[:64],
                is_update_available=bool(meta.get("is_update_available", False)),
                installed_date=now,
                update_version=str(meta.get("update_version") or "")[:300] or None,
            )
        )


async def _sync_services(db: AsyncSession, server_id: str, services: Dict[str, Any]) -> None:
    now = datetime.utcnow()
    for svc_name, raw_val in services.items():
        name = str(svc_name)[:300]
        # Support both old str format and new dict format from agent
        if isinstance(raw_val, dict):
            status = _norm_service_status(str(raw_val.get("status", "")))
            sub_state = str(raw_val.get("sub_state", ""))[:100] or None
            enabled = str(raw_val.get("enabled", ""))[:50] or None
            description = str(raw_val.get("description", ""))[:500] or None
        else:
            status = _norm_service_status(str(raw_val))
            sub_state = None
            enabled = None
            description = None

        result = await db.execute(
            select(SaltServiceState).where(
                SaltServiceState.server_id == server_id,
                SaltServiceState.service_name == name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            prev = existing.status
            status_changed = prev != status
            existing.previous_status = prev if status_changed else existing.previous_status
            existing.status = status
            existing.sub_state = sub_state
            if enabled is not None:
                existing.enabled = enabled
            if description is not None:
                existing.description = description
            existing.last_checked = now
            if status_changed:
                existing.status_changed_at = now
        else:
            db.add(
                SaltServiceState(
                    id=f"srv_{uuid4().hex}"[:180],
                    server_id=server_id,
                    service_name=name,
                    status=status,
                    previous_status=None,
                    sub_state=sub_state,
                    enabled=enabled,
                    description=description,
                    last_checked=now,
                    status_changed_at=now,
                )
            )


async def _sync_logs(db: AsyncSession, server_id: str, logs: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    added = 0
    for entry in logs[:200]:
        if not isinstance(entry, dict):
            continue
        lid = f"log_{server_id}_{uuid4().hex}"
        ts_raw = entry.get("timestamp") or entry.get("time")
        ts = now
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                pass
        lvl = str(entry.get("level") or entry.get("log_level") or "INFO").upper()
        meta = {
            k: v
            for k, v in entry.items()
            if k not in ("timestamp", "time", "level", "log_level", "source", "message")
        }
        db.add(
            SaltLog(
                id=lid[:180],
                server_id=server_id,
                timestamp=ts,
                log_level=lvl[:16],
                source=str(entry.get("source") or "minion")[:200],
                message=str(entry.get("message") or "")[:16000],
                extra=meta or None,
            )
        )
        added += 1

    # Trim oldest beyond 10k rows per server to bound storage
    if added > 0:
        subq = (
            select(SaltLog.id)
            .where(SaltLog.server_id == server_id)
            .order_by(SaltLog.timestamp.desc())
            .offset(10000)
            .scalar_subquery()
        )
        await db.execute(
            delete(SaltLog).where(SaltLog.server_id == server_id).where(SaltLog.id.in_(subq))
        )


async def _sync_events(db: AsyncSession, server_id: str, events: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow()
    for ev in events[:50]:
        if not isinstance(ev, dict):
            continue
        tag = str(ev.get("event_tag") or "opspilot/minion")[:300]
        etype = str(ev.get("event_type") or ev.get("alert_type") or "notice")[:120]
        data = ev.get("event_data") if isinstance(ev.get("event_data"), dict) else {}
        if not data:
            data = {
                "message": ev.get("message"),
                "severity": ev.get("severity"),
            }
        db.add(
            SaltEvent(
                server_id=server_id,
                event_tag=tag,
                event_type=etype,
                event_data=json.loads(json.dumps(data)),
                processed=False,
                created_at=now,
            )
        )


async def apply_agent_push_payload(
    db: AsyncSession,
    server: Server,
    *,
    metrics: Dict[str, Any],
    host_profile: Optional[Dict[str, Any]] = None,
    processes: Optional[List[Dict[str, Any]]] = None,
    services: Optional[Dict[str, str]] = None,
    packages: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    logs: Optional[List[Dict[str, Any]]] = None,
    events: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Persist push payload side-effects (metrics sample always when metrics non-empty)."""
    now = datetime.utcnow()

    if metrics:
        await metrics_push_service.insert_push_sample(db, server_id=server.id, payload=metrics)

    if host_profile:
        _apply_host_profile(server, host_profile, now)

    if processes is not None:
        await _sync_processes(db, server.id, processes)

    if packages is not None:
        pkgs = normalize_packages_data(packages)
        await _sync_packages(db, server.id, pkgs)

    if services is not None:
        await _sync_services(db, server.id, services)

    if logs is not None:
        await _sync_logs(db, server.id, logs)

    if events is not None:
        await _sync_events(db, server.id, events)

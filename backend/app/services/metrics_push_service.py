"""Persist and read agent-pushed metrics samples."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.server import Server
from app.models.server_metrics_push import ServerMetricsPushSample

# GET /metrics prefers push payload when newer than this age
PUSH_FRESHNESS = timedelta(minutes=5)


async def insert_push_sample(
    db: AsyncSession,
    *,
    server_id: str,
    payload: Dict[str, Any],
) -> None:
    row = ServerMetricsPushSample(
        id=str(uuid4()),
        server_id=server_id,
        recorded_at=datetime.utcnow(),
        payload=payload,
    )
    db.add(row)


async def mark_agent_seen(db: AsyncSession, server: Server) -> None:
    server.agent_last_seen_at = datetime.utcnow()
    if server.status != "error" and server.status in (
        "provisioning",
        "installing_agent",
        "connecting",
    ):
        server.status = "online"
    server.updated_at = datetime.utcnow()


async def get_latest_push_sample(
    db: AsyncSession,
    server_id: str,
) -> Optional[Tuple[datetime, Dict[str, Any]]]:
    q = (
        select(ServerMetricsPushSample)
        .where(ServerMetricsPushSample.server_id == server_id)
        .order_by(desc(ServerMetricsPushSample.recorded_at))
        .limit(1)
    )
    r = await db.execute(q)
    row = r.scalar_one_or_none()
    if row is None:
        return None
    return row.recorded_at, dict(row.payload)


async def get_fresh_push_metrics(
    db: AsyncSession,
    server_id: str,
) -> Optional[Dict[str, Any]]:
    latest = await get_latest_push_sample(db, server_id)
    if latest is None:
        return None
    recorded_at, payload = latest
    if datetime.utcnow() - recorded_at > PUSH_FRESHNESS:
        return None
    return payload

"""Run agent SSH install after HTTP response (separate asyncio loop + DB session)."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from app.services.agent_ssh_install import install_with_settings

logger = logging.getLogger(__name__)


async def _update_server_install_outcome(server_id: str, ok: bool, err: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            r = await db.execute(select(Server).where(Server.id == server_id))
            server = r.scalar_one_or_none()
            if not server:
                return
            if ok:
                server.status = "online"
            else:
                server.status = "error"
            await db.commit()
        except Exception as e:
            logger.error("Failed to persist install outcome for %s: %s", server_id, e)
            await db.rollback()


def schedule_agent_install(
    *,
    server_id: str,
    organization_id: str,
    ip_address: str,
    agent_api_key: str,
    ssh_username: str,
    ssh_password: str,
    ssh_port: int = 22,
) -> None:
    """Synchronous entrypoint for FastAPI BackgroundTasks."""

    async def runner() -> None:
        ok, err = await asyncio.to_thread(
            install_with_settings,
            host=ip_address,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            server_id=server_id,
            organization_id=organization_id,
            agent_api_key=agent_api_key,
        )
        await _update_server_install_outcome(server_id, ok, err)

    asyncio.run(runner())

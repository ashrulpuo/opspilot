"""Run Salt minion SSH install after HTTP response (FastAPI BackgroundTasks, same event loop as DB)."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from app.services.agent_ssh_install import install_with_settings
from app.services.server_service import server_service

logger = logging.getLogger(__name__)

# Bootstrap + package install + systemd can be slow on cold networks.
_INSTALL_TIMEOUT_SEC = 960.0


async def _update_server_install_outcome(server_id: str, ok: bool, err: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            r = await db.execute(select(Server).where(Server.id == server_id))
            server = r.scalar_one_or_none()
            if not server:
                return
            if ok:
                server.status = "online"
                server.agent_install_last_error = None
            else:
                server.status = "error"
                server.agent_install_last_error = (err or "")[:8000] or "Install failed (no details)"
            await db.commit()
            if not ok and err:
                logger.warning("Salt minion install failed server_id=%s: %s", server_id, err)
        except Exception as e:
            logger.error("Failed to persist install outcome for %s: %s", server_id, e)
            await db.rollback()


async def schedule_agent_install(
    *,
    server_id: str,
    organization_id: str,
    ip_address: str,
    agent_api_key: str,
    ssh_username: str,
    ssh_password: str,
    ssh_port: int = 22,
) -> None:
    """Async entrypoint for FastAPI ``BackgroundTasks`` — must not use ``asyncio.run()`` (breaks async DB)."""
    # Push the current API key (and org/base URL) to the Salt master pillar first so the minion
    # can authenticate to OpsPilot after we run ``opspilot_snapshot``/``opspilot_metrics`` on the host.
    try:
        async with AsyncSessionLocal() as db:
            r = await db.execute(select(Server).where(Server.id == server_id))
            server = r.scalar_one_or_none()
            if server:
                await server_service._setup_salt_minion(
                    server_id,
                    server.hostname,
                    server.ip_address,
                    organization_id,
                    agent_api_key,
                )
    except Exception as e:
        logger.warning(
            "Salt pillar could not be updated before SSH (minion may use stale key): server_id=%s: %s",
            server_id,
            e,
        )

    ok: bool
    err: str
    try:
        ok, err = await asyncio.wait_for(
            asyncio.to_thread(
                install_with_settings,
                host=ip_address,
                port=ssh_port,
                username=ssh_username,
                password=ssh_password,
                server_id=server_id,
                organization_id=organization_id,
                agent_api_key=agent_api_key,
            ),
            timeout=_INSTALL_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        logger.error("Salt minion SSH install timed out server_id=%s host=%s", server_id, ip_address)
        ok, err = False, "SSH install timed out (network, firewall, or slow bootstrap on target)"
    except Exception as e:
        logger.exception("Salt minion SSH install crashed server_id=%s", server_id)
        ok, err = False, str(e)
    await _update_server_install_outcome(server_id, ok, err)

"""SSH-based deployment of the OpsPilot push agent (Linux targets)."""
from __future__ import annotations

import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Tuple

import paramiko

from app.core.config import get_settings

logger = logging.getLogger(__name__)

BUNDLE_DIR = Path(__file__).resolve().parent / "agent_bundle"


def _exec(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> None:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if exit_status != 0:
        raise RuntimeError(f"Remote command failed ({exit_status}): {cmd}\n{err or out}")


def install_agent_via_ssh(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    api_base_url: str,
    server_id: str,
    organization_id: str,
    agent_api_key: str,
    interval_seconds: int = 60,
) -> Tuple[bool, str]:
    """Copy agent bundle, write config, enable systemd. Requires sudo without TTY or root SSH."""
    agent_py = BUNDLE_DIR / "opspilot-agent.py"
    unit_file = BUNDLE_DIR / "opspilot-agent.service"
    if not agent_py.is_file() or not unit_file.is_file():
        return False, "Agent bundle files missing on API host"

    cfg = {
        "api_base_url": api_base_url.rstrip("/"),
        "server_id": server_id,
        "organization_id": organization_id,
        "api_key": agent_api_key,
        "interval_seconds": interval_seconds,
    }
    cfg_bytes = json.dumps(cfg, indent=2).encode("utf-8")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sp = "" if username == "root" else "sudo "
    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=60,
            banner_timeout=60,
            auth_timeout=60,
        )
        _exec(
            client,
            f"{sp}mkdir -p /opt/opspilot/bin /opt/opspilot/config /var/log/opspilot "
            "|| mkdir -p /opt/opspilot/bin /opt/opspilot/config /var/log/opspilot",
        )
        sftp = client.open_sftp()
        try:
            with agent_py.open("rb") as f:
                sftp.putfo(f, "/opt/opspilot/bin/opspilot-agent.py")
            sftp.putfo(BytesIO(cfg_bytes), "/opt/opspilot/config/agent.json")
            with unit_file.open("rb") as f:
                sftp.putfo(f, "/tmp/opspilot-agent.service")
        finally:
            sftp.close()

        _exec(
            client,
            f"{sp}chmod 755 /opt/opspilot/bin/opspilot-agent.py 2>/dev/null || chmod 755 /opt/opspilot/bin/opspilot-agent.py",
        )
        _exec(
            client,
            f"{sp}cp /tmp/opspilot-agent.service /etc/systemd/system/opspilot-agent.service "
            f"&& {sp}chmod 644 /etc/systemd/system/opspilot-agent.service "
            f"&& {sp}systemctl daemon-reload "
            f"&& {sp}systemctl enable opspilot-agent.service "
            f"&& {sp}systemctl restart opspilot-agent.service",
            timeout=180,
        )
        logger.info("Agent SSH install completed for server_id=%s host=%s", server_id, host)
        return True, ""
    except Exception as e:
        logger.warning("Agent SSH install failed for server_id=%s: %s", server_id, e)
        return False, str(e)
    finally:
        client.close()


def install_with_settings(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    server_id: str,
    organization_id: str,
    agent_api_key: str,
    interval_seconds: int = 60,
) -> Tuple[bool, str]:
    settings = get_settings()
    return install_agent_via_ssh(
        host=host,
        port=port,
        username=username,
        password=password,
        api_base_url=settings.PUBLIC_API_BASE_URL,
        server_id=server_id,
        organization_id=organization_id,
        agent_api_key=agent_api_key,
        interval_seconds=interval_seconds,
    )

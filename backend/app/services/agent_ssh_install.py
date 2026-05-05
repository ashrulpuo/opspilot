"""SSH-based installation of Salt minion (Linux targets) for OpsPilot."""
from __future__ import annotations

import logging
import secrets
import shlex
from io import BytesIO
from typing import Tuple

import paramiko

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ``bootstrap.saltproject.io`` was decommissioned (Salt Project uses GitHub Releases now).
_SALT_BOOTSTRAP_SH_URL = (
    "https://github.com/saltstack/salt-bootstrap/releases/latest/download/bootstrap-salt.sh"
)


def _run_opspilot_post_install_refresh(client: paramiko.SSHClient, sp: str) -> None:
    """Sync execution modules from the Salt master + apply cron schedule so new ``_modules`` apply.

    Runs after every install/reinstall (even when bootstrap was skipped because salt-minion was already
    present). Failures are logged but do not fail SSH install — master may lack states yet."""
    steps = (
        ("salt-call saltutil.sync_modules", 300),
        ("salt-call state.apply base.opspilot.salt_metrics_schedule", 600),
    )
    for cmd, timeout_sec in steps:
        try:
            _exec(client, f"{sp}{cmd}", timeout=timeout_sec)
            logger.info("Post-install Salt step OK: %s", cmd.split()[1])
        except Exception as e:
            logger.warning(
                "Post-install Salt step skipped or failed (%s): %s",
                cmd[:80],
                e,
            )


def _exec(client: paramiko.SSHClient, cmd: str, timeout: int = 900) -> None:
    """Run a **single-line** shell command via login bash (PTY). Multiline logic must run from a remote file (see install)."""
    inner = shlex.quote(cmd)
    # ``bash --login`` loads the same profile/rc as an interactive SSH login; ``get_pty`` matches a TTY session.
    wrapped = f"exec bash --login -o pipefail -c {inner}"
    stdin, stdout, stderr = client.exec_command(
        wrapped,
        timeout=timeout,
        get_pty=True,
        environment={"TERM": "xterm-256color", "LANG": "C.UTF-8"},
    )
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if exit_status != 0:
        combined = (err + out).strip() or "(no output)"
        raise RuntimeError(f"Remote command failed ({exit_status}): {cmd}\n{combined}")


def install_salt_minion_via_ssh(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    salt_master: str,
    minion_id: str,
) -> Tuple[bool, str]:
    """Install ``salt-minion`` if missing, write minion id + master, enable and restart service.

    Minion ``id`` must match OpsPilot Salt pillar naming: ``opspilot-minion-{server_uuid}``.
    Requires passwordless ``sudo`` for non-root users (same as prior push-agent install).
    """
    master = (salt_master or "").strip()
    if not master:
        return False, "SALT_MASTER_HOST is not set on the API (configure backend environment)"

    mid = (minion_id or "").strip()
    if not mid:
        return False, "minion_id is required"

    minion_conf = f"master: {master}\nid: {mid}\n".encode("utf-8")

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

        # Non-interactive SSH often uses a minimal PATH (no /usr/local/bin) — expand before probing curl.
        # Resolve curl/wget by common paths + PATH (POSIX /bin/sh safe for paramiko default shell).
        bootstrap = f"""set -eu
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
if command -v salt-minion >/dev/null 2>&1; then
  exit 0
fi
CURL_BIN=""
for c in $(command -v curl 2>/dev/null || true) /usr/bin/curl /bin/curl /usr/local/bin/curl; do
  [ -n "$c" ] || continue
  [ -x "$c" ] || continue
  CURL_BIN="$c"
  break
done
WGET_BIN=""
for w in $(command -v wget 2>/dev/null || true) /usr/bin/wget /bin/wget /usr/local/bin/wget; do
  [ -n "$w" ] || continue
  [ -x "$w" ] || continue
  WGET_BIN="$w"
  break
done
if [ -z "$CURL_BIN" ] && [ -z "$WGET_BIN" ]; then
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    {sp}apt-get update -qq && {sp}apt-get install -y -qq curl ca-certificates
  elif command -v apk >/dev/null 2>&1; then
    {sp}apk add --no-cache curl ca-certificates
  elif command -v dnf >/dev/null 2>&1; then
    {sp}dnf install -y -q curl ca-certificates || true
  elif command -v yum >/dev/null 2>&1; then
    {sp}yum install -y -q curl ca-certificates || true
  fi
  for c in $(command -v curl 2>/dev/null || true) /usr/bin/curl /bin/curl /usr/local/bin/curl; do
    [ -n "$c" ] || continue
    [ -x "$c" ] || continue
    CURL_BIN="$c"
    break
  done
  for w in $(command -v wget 2>/dev/null || true) /usr/bin/wget /bin/wget /usr/local/bin/wget; do
    [ -n "$w" ] || continue
    [ -x "$w" ] || continue
    WGET_BIN="$w"
    break
  done
fi
# Bootstrap v2026+ parses ``stable <rev>`` where ``<rev>`` is ``latest``, ``3006``, or ``3007`` — not ``minion``.
# Salt minion is installed by default; ``-M`` adds master.
if [ -n "$CURL_BIN" ]; then
  "$CURL_BIN" -fsSL {_SALT_BOOTSTRAP_SH_URL} | {sp}bash -s -- stable latest
elif [ -n "$WGET_BIN" ]; then
  "$WGET_BIN" -qO- {_SALT_BOOTSTRAP_SH_URL} | {sp}bash -s -- stable latest
else
  echo 'salt-minion is not installed and curl/wget not found after PATH fix and package install attempt' >&2
  exit 1
fi
"""
        # Do not feed multiline scripts on stdin with ``get_pty=True``: bash becomes interactive (prompts,
        # bracketed-paste noise). Do not pipe Salt bootstrap to ``sh`` on Ubuntu (dash): ``Syntax error: newline``.
        remote_sh = f"/tmp/opspilot-salt-bootstrap-{secrets.token_hex(8)}.sh"
        sftp_boot = client.open_sftp()
        try:
            sftp_boot.putfo(BytesIO(bootstrap.encode("utf-8")), remote_sh)
        finally:
            sftp_boot.close()
        qpath = shlex.quote(remote_sh)
        try:
            _exec(client, f"{sp}chmod 700 {qpath}")
            _exec(client, f"{sp}bash --login -o pipefail {qpath}", timeout=900)
        finally:
            try:
                _exec(client, f"{sp}rm -f {qpath}", timeout=60)
            except Exception:
                logger.debug("Could not remove remote bootstrap script %s", remote_sh, exc_info=True)

        _exec(client, f"{sp}mkdir -p /etc/salt/minion.d")
        sftp = client.open_sftp()
        try:
            sftp.putfo(BytesIO(minion_conf), "/tmp/99-opspilot-minion.conf")
        finally:
            sftp.close()

        _exec(
            client,
            f"{sp}mv /tmp/99-opspilot-minion.conf /etc/salt/minion.d/99-opspilot.conf "
            f"&& {sp}chmod 644 /etc/salt/minion.d/99-opspilot.conf "
            f"&& {sp}systemctl enable salt-minion "
            f"&& {sp}systemctl restart salt-minion",
            timeout=180,
        )

        _run_opspilot_post_install_refresh(client, sp)

        logger.info("Salt minion SSH install completed for host=%s minion_id=%s", host, mid)
        return True, ""
    except Exception as e:
        logger.warning("Salt minion SSH install failed for host=%s: %s", host, e)
        return False, str(e)
    finally:
        client.close()


def _deploy_agent_config(
    client: paramiko.SSHClient,
    *,
    sp: str,
    server_id: str,
    organization_id: str,
    agent_api_key: str,
    api_base_url: str,
    interval_seconds: int = 5,
) -> None:
    """Write agent config + script to remote host and ensure systemd service is running.

    Uses an existing open paramiko client. Failures propagate to caller.
    """
    import json as _json
    from pathlib import Path as _Path

    config_bytes = _json.dumps(
        {
            "api_base_url": api_base_url.rstrip("/"),
            "server_id": server_id,
            "organization_id": organization_id,
            "api_key": agent_api_key,
            "interval_seconds": interval_seconds,
        },
        indent=2,
    ).encode("utf-8")

    agent_src = _Path(__file__).parent / "agent_bundle" / "opspilot-agent.py"
    agent_bytes = agent_src.read_bytes()

    service_unit = b"""[Unit]
Description=OpsPilot push agent
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/opspilot/bin/opspilot-agent.py
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
"""

    _exec(client, f"{sp}mkdir -p /opt/opspilot/config /opt/opspilot/bin")

    sftp = client.open_sftp()
    try:
        sftp.putfo(BytesIO(config_bytes), "/tmp/opspilot-agent.json")
        sftp.putfo(BytesIO(agent_bytes), "/tmp/opspilot-agent.py")
        sftp.putfo(BytesIO(service_unit), "/tmp/opspilot-agent.service")
    finally:
        sftp.close()

    _exec(
        client,
        f"{sp}mv /tmp/opspilot-agent.json /opt/opspilot/config/agent.json"
        f" && {sp}chmod 600 /opt/opspilot/config/agent.json",
    )
    _exec(
        client,
        f"{sp}mv /tmp/opspilot-agent.py /opt/opspilot/bin/opspilot-agent.py"
        f" && {sp}chmod 755 /opt/opspilot/bin/opspilot-agent.py",
    )
    _exec(
        client,
        f"{sp}mv /tmp/opspilot-agent.service /etc/systemd/system/opspilot-agent.service"
        f" && {sp}chmod 644 /etc/systemd/system/opspilot-agent.service"
        f" && {sp}systemctl daemon-reload"
        f" && {sp}systemctl enable opspilot-agent"
        f" && {sp}systemctl restart opspilot-agent",
        timeout=60,
    )
    logger.info("Push agent deployed server_id=%s", server_id)


def install_with_settings(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    server_id: str,
    organization_id: str,
    agent_api_key: str,
    interval_seconds: int = 5,
) -> Tuple[bool, str]:
    """Install Salt minion then deploy OpsPilot push agent with correct API key."""
    settings = get_settings()
    minion_id = f"opspilot-minion-{server_id}"

    ok, err = install_salt_minion_via_ssh(
        host=host,
        port=port,
        username=username,
        password=password,
        salt_master=settings.SALT_MASTER_HOST,
        minion_id=minion_id,
    )
    if not ok:
        return ok, err

    sp = "" if username == "root" else "sudo "
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host, port=port, username=username, password=password,
            timeout=60, banner_timeout=60, auth_timeout=60,
        )
        _deploy_agent_config(
            client,
            sp=sp,
            server_id=server_id,
            organization_id=organization_id,
            agent_api_key=agent_api_key,
            api_base_url=settings.PUBLIC_API_BASE_URL,
            interval_seconds=interval_seconds,
        )
    except Exception as e:
        # Salt install succeeded — log agent deploy failure but don't fail the whole install.
        logger.warning("Push agent deploy failed (Salt minion OK) host=%s: %s", host, e)
    finally:
        client.close()

    return True, ""


def deploy_push_agent_only(
    *,
    host: str,
    port: int = 22,
    username: str,
    password: str,
    server_id: str,
    organization_id: str,
    agent_api_key: str,
    interval_seconds: int = 5,
) -> tuple[bool, str]:
    """SSH into host and (re)deploy only the push agent script + config + systemd service.

    Does NOT install Salt minion. Safe to call on an already-provisioned server.
    """
    settings = get_settings()
    sp = "" if username == "root" else "sudo "
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host, port=port, username=username, password=password,
            timeout=60, banner_timeout=60, auth_timeout=60,
        )
        _deploy_agent_config(
            client,
            sp=sp,
            server_id=server_id,
            organization_id=organization_id,
            agent_api_key=agent_api_key,
            api_base_url=settings.PUBLIC_API_BASE_URL,
            interval_seconds=interval_seconds,
        )
        return True, ""
    except Exception as e:
        logger.warning("Push agent redeploy failed host=%s: %s", host, e)
        return False, str(e)
    finally:
        client.close()

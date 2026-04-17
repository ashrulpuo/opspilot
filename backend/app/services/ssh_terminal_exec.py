"""Blocking SSH helpers for the browser terminal (use via ``asyncio.to_thread``)."""

from __future__ import annotations

import logging
import shlex
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger(__name__)


def paramiko_connect(
    host: str,
    port: int,
    username: str,
    password: str,
    *,
    timeout: int = 30,
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        timeout=timeout,
        banner_timeout=timeout,
        auth_timeout=timeout,
    )
    return client


def open_interactive_shell(
    client: paramiko.SSHClient,
    *,
    term: str = "xterm-256color",
    cols: int = 120,
    rows: int = 32,
) -> paramiko.Channel:
    """Allocate a PTY and start the user's login shell (like ``ssh -t``)."""
    transport = client.get_transport()
    if transport is None:
        raise RuntimeError("SSH transport not ready")
    ch = transport.open_session()
    ch.get_pty(term, width=int(cols), height=int(rows))
    ch.invoke_shell()
    return ch


def channel_resize_pty(channel: paramiko.Channel, cols: int, rows: int) -> None:
    channel.resize_pty(width=max(8, min(int(cols), 500)), height=max(2, min(int(rows), 500)))


def channel_send_text(channel: paramiko.Channel, text: str) -> None:
    data = text.encode("utf-8")
    while data:
        n = channel.send(data)
        data = data[n:]


def channel_recv_chunk(channel: paramiko.Channel, nbytes: int = 65536) -> bytes:
    return channel.recv(nbytes)


def paramiko_exec(client: paramiko.SSHClient, command: str, *, timeout: int = 120) -> Tuple[int, str, str]:
    """Run one line on the remote host via ``bash -lc`` (no PTY — for non-interactive tools)."""
    wrapped = f"bash -lc {shlex.quote(command)}"
    _stdin, stdout, stderr = client.exec_command(wrapped, timeout=timeout, get_pty=False)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return exit_status, out, err


def paramiko_close(client: Optional[paramiko.SSHClient]) -> None:
    if client is None:
        return
    try:
        client.close()
    except Exception as e:
        logger.debug("paramiko close: %s", e)

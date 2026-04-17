"""SSH terminal API endpoints for OpsPilot."""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.security import get_current_user
from app.models.ssh_session import SSHSesion
from app.services.server_service import server_service
from app.services.ssh_terminal_exec import (
    channel_recv_chunk,
    channel_resize_pty,
    channel_send_text,
    open_interactive_shell,
    paramiko_close,
    paramiko_connect,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Active SSH sessions (in-memory storage)
# TODO: Move to Redis for production
active_sessions: Dict[str, Dict[str, Any]] = {}


async def _bridge_websocket_pty(websocket: WebSocket, channel: Any) -> None:
    """Bidirectional copy: browser WebSocket ↔ Paramiko PTY channel (real interactive SSH)."""

    async def chan_to_ws() -> None:
        try:
            while True:
                chunk = await asyncio.to_thread(channel_recv_chunk, channel, 65536)
                if not chunk:
                    break
                await websocket.send_text(chunk.decode("utf-8", errors="replace"))
        except (WebSocketDisconnect, RuntimeError, OSError) as e:
            logger.debug("SSH PTY upstream closed: %s", e)

    async def ws_to_chan() -> None:
        try:
            while True:
                message = await websocket.receive()
                mtype = message.get("type")
                if mtype == "websocket.disconnect":
                    break
                if mtype != "websocket.receive":
                    continue
                if "bytes" in message:
                    data = message["bytes"].decode("utf-8", errors="replace")
                elif "text" in message:
                    data = message["text"]
                else:
                    continue

                if data.startswith("{") and '"type"' in data:
                    try:
                        obj = json.loads(data)
                        if obj.get("type") == "resize":
                            rows = int(obj.get("rows") or 24)
                            cols = int(obj.get("cols") or 80)
                            await asyncio.to_thread(channel_resize_pty, channel, cols, rows)
                    except (ValueError, TypeError, json.JSONDecodeError):
                        pass
                    continue

                await asyncio.to_thread(channel_send_text, channel, data)
        except WebSocketDisconnect:
            pass

    upstream = asyncio.create_task(chan_to_ws())
    downstream = asyncio.create_task(ws_to_chan())
    tasks = {upstream, downstream}
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


class SSHSessionCreateRequest(BaseModel):
    """SSH session creation request schema."""

    server_id: str


class SSHSessionResponse(BaseModel):
    """SSH session response schema."""

    session_id: str
    server_id: str
    status: str


@router.post("/servers/{server_id}/ssh/sessions", response_model=SSHSessionResponse)
async def create_ssh_session(
    server_id: str,
    request: SSHSessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new SSH session to a server.

    Args:
        server_id: Server ID
        request: SSH session request
        db: Database session
        current_user: Current authenticated user

    Returns:
        SSH session details

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    # Check server permission
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

    # Create SSH session
    session_id = str(uuid.uuid4())
    ssh_session = SSHSesion(
        id=session_id,
        server_id=server_id,
        organization_id=server.organization_id,
        user_id=user_id,
        status="active",
    )

    db.add(ssh_session)
    await db.commit()

    # Store in active sessions
    active_sessions[session_id] = {
        "server_id": server_id,
        "user_id": user_id,
        "status": "active",
        "websocket": None,  # Will be set when WebSocket connects
        "ssh_connection": None,  # Will be set when WebSocket connects
    }

    logger.info(f"Created SSH session {session_id} for server {server_id}")

    return SSHSessionResponse(
        session_id=session_id,
        server_id=server_id,
        status="active",
    )


@router.get("/servers/{server_id}/ssh/sessions")
async def list_ssh_sessions(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all SSH sessions for a server.

    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of SSH sessions

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    # Check server permission
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

    # Get SSH sessions
    from sqlalchemy import select

    result = await db.execute(
        select(SSHSesion).where(SSHSesion.server_id == server_id)
    )
    sessions = result.scalars().all()

    return {
        "server_id": server_id,
        "sessions": [
            {
                "id": session.id,
                "user_id": session.user_id,
                "status": session.status,
                "started_at": session.created_at.isoformat() if session.created_at else None,
                "ended_at": session.terminated_at.isoformat() if session.terminated_at else None,
            }
            for session in sessions
        ],
    }


@router.post("/ssh/sessions/{session_id}/terminate")
async def terminate_ssh_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Terminate an active SSH session.

    Args:
        session_id: SSH session ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Termination result

    Raises:
        HTTPException: If session not found or no permission
    """
    user_id = current_user["id"]

    # Get SSH session
    from sqlalchemy import select

    result = await db.execute(
        select(SSHSesion).where(SSHSesion.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH session not found",
        )

    # Check permission
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to terminate this session",
        )

    # Terminate session
    if session_id in active_sessions:
        # Close WebSocket if open
        if active_sessions[session_id].get("websocket"):
            try:
                await active_sessions[session_id]["websocket"].close()
            except Exception as e:
                logger.warning(f"Failed to close WebSocket: {e}")

        del active_sessions[session_id]

    # Update database
    session.status = "terminated"
    session.terminated_at = datetime.now(timezone.utc)
    session.terminated_reason = "user"
    await db.commit()

    logger.info(f"Terminated SSH session {session_id}")

    return {
        "message": "SSH session terminated",
        "session_id": session_id,
    }


@router.websocket("/ssh/terminal/{session_id}")
async def ssh_terminal_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket ↔ SSH: with credentials, uses a real PTY + shell like ``ssh -t``."""
    await websocket.accept()

    bridge_channel: Any = None
    bridge_client: Any = None

    try:
        if session_id not in active_sessions:
            await websocket.close(code=1008, reason="Session not found")
            return

        session_info = active_sessions[session_id]
        server_id = session_info["server_id"]
        user_id = session_info["user_id"]

        session_info["websocket"] = websocket

        server = None
        creds = None
        async with AsyncSessionLocal() as db:
            server = await server_service.get_server(db, server_id, user_id)
            creds = await server_service.get_decrypted_ssh_credentials(db, server_id, user_id)

        used_pty = False
        if server and creds:
            username, port, password = creds
            host = server.ip_address
            try:
                bridge_client = await asyncio.to_thread(
                    paramiko_connect,
                    host,
                    port,
                    username,
                    password,
                )
                session_info["paramiko_client"] = bridge_client
                bridge_channel = await asyncio.to_thread(open_interactive_shell, bridge_client)
                await websocket.send_text(
                    f"\r\n\x1b[32mInteractive SSH (PTY) as {username} @ {host}:{port} "
                    f"(TERM=xterm-256color)\x1b[0m\r\n"
                )
                await _bridge_websocket_pty(websocket, bridge_channel)
                used_pty = True
            except Exception as e:
                logger.warning("SSH terminal PTY failed server_id=%s: %s", server_id, e)
                await websocket.send_text(f"\r\n\x1b[31mSSH session failed: {e}\x1b[0m\r\n")
                if bridge_channel is not None:
                    try:
                        await asyncio.to_thread(lambda ch=bridge_channel: ch.close())
                    except Exception:
                        pass
                    bridge_channel = None
                if bridge_client is not None:
                    await asyncio.to_thread(paramiko_close, bridge_client)
                    bridge_client = None
                session_info.pop("paramiko_client", None)
        elif server:
            await websocket.send_text(
                "\r\n\x1b[33mNo SSH credentials on this server. "
                "Edit the server and set SSH user + password for a full terminal.\x1b[0m\r\n"
            )

        if not used_pty:
            shell_prompt = f"{server.hostname}$ " if server else f"{server_id[:8]}…$ "
            session_info["prompt_str"] = shell_prompt
            title = server.hostname if server else server_id
            await websocket.send_text(f"OpsPilot SSH (local) — {title}\r\n\r\n")
            await websocket.send_text(shell_prompt)

            buffer = ""
            while True:
                data = await websocket.receive_text()

                if data.startswith("{") and '"type"' in data:
                    continue

                if data.startswith("\x1b"):
                    await websocket.send_text(data)
                    continue

                exit_session = False
                for c in data:
                    if c in ("\r", "\n"):
                        command = buffer.strip()
                        buffer = ""

                        if command == "exit":
                            await websocket.send_text("\r\nGoodbye!\r\n")
                            exit_session = True
                            break
                        if command == "clear":
                            await websocket.send_text("\033[2J\033[H")
                            await websocket.send_text(session_info["prompt_str"])
                            continue

                        await websocket.send_text("\r\n")
                        if command:
                            await websocket.send_text(
                                "(no live SSH — add SSH credentials on the server)\r\n"
                            )
                        await websocket.send_text(session_info["prompt_str"])

                    elif c in ("\x7f", "\x08"):
                        if buffer:
                            buffer = buffer[:-1]
                            await websocket.send_text("\b \b")

                    else:
                        buffer += c
                        await websocket.send_text(c)

                if exit_session:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        except Exception:
            pass

    finally:
        if bridge_channel is not None:
            try:
                await asyncio.to_thread(lambda ch=bridge_channel: ch.close())
            except Exception:
                pass
        if session_id in active_sessions:
            del active_sessions[session_id]
        if bridge_client is not None:
            try:
                await asyncio.to_thread(paramiko_close, bridge_client)
            except Exception as e:
                logger.debug("paramiko_close: %s", e)

        from sqlalchemy import select

        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SSHSesion).where(SSHSesion.id == session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    session.status = "terminated"
                    session.terminated_at = datetime.now(timezone.utc)
                    session.terminated_reason = "disconnect"
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")

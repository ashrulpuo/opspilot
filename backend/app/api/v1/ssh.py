"""SSH terminal API endpoints for OpsPilot."""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ssh_session import SSHSesion
from app.services.server_service import server_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Active SSH sessions (in-memory storage)
# TODO: Move to Redis for production
active_sessions: Dict[str, Dict[str, Any]] = {}


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

    # Check concurrent session limit
    from sqlalchemy import select

    result = await db.execute(
        select(SSHSesion).where(
            SSHSesion.server_id == server_id,
            SSHSesion.status == "active",
        )
    )
    active_sessions_count = len(result.scalars().all())

    if active_sessions_count >= 3:  # Default concurrent session limit
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Concurrent session limit reached",
        )

    # Create SSH session
    session_id = str(uuid.uuid4())
    ssh_session = SSHSesion(
        id=session_id,
        server_id=server_id,
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
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
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
    from datetime import datetime
    session.ended_at = datetime.utcnow()
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
    """WebSocket endpoint for SSH terminal streaming.

    This endpoint provides real-time SSH terminal access via WebSocket,
    compatible with xterm.js frontend.

    Args:
        websocket: WebSocket connection
        session_id: SSH session ID
    """
    await websocket.accept()

    try:
        # Get SSH session info
        if session_id not in active_sessions:
            await websocket.close(code=1008, reason="Session not found")
            return

        session_info = active_sessions[session_id]
        server_id = session_info["server_id"]

        # TODO: Establish SSH connection to server via Salt
        # This would use Salt's ssh execution module or direct SSH
        # For now, we simulate the terminal

        session_info["websocket"] = websocket

        # Send welcome message
        await websocket.send_text(f"\r\nConnected to server: {server_id}\r\n")
        await websocket.send_text("OpsPilot SSH Terminal v1.0\r\n\r\n")
        await websocket.send_text(f"{server_id}$ ")

        # Terminal I/O loop
        buffer = ""
        while True:
            data = await websocket.receive_text()

            # Handle special terminal sequences
            if data == "\r":  # Enter key
                command = buffer.strip()
                buffer = ""

                # Send command to SSH (simulated for now)
                if command == "exit":
                    await websocket.send_text("\r\nGoodbye!\r\n")
                    break
                elif command == "clear":
                    await websocket.send_text("\033[2J\033[H")
                    await websocket.send_text(f"{server_id}$ ")
                    continue
                else:
                    # Simulate command execution
                    await websocket.send_text(f"\r\n")
                    await websocket.send_text(f"Executed: {command}\r\n")

                await websocket.send_text(f"{server_id}$ ")

            elif data == "\x7f":  # Backspace
                if buffer:
                    buffer = buffer[:-1]
                    await websocket.send_text("\b \b")

            elif data.startswith("\x1b"):  # Escape sequences (arrow keys, etc.)
                # Handle escape sequences
                await websocket.send_text(data)

            elif len(data) == 1:  # Regular character
                buffer += data
                await websocket.send_text(data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        except:
            pass

    finally:
        # Cleanup
        if session_id in active_sessions:
            session_info = active_sessions[session_id]
            session_info["status"] = "closed"
            del active_sessions[session_id]

        # Update database
        from sqlalchemy import select
        from datetime import datetime

        try:
            db = next(get_db())
            result = await db.execute(
                select(SSHSesion).where(SSHSesion.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = "closed"
                session.ended_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")

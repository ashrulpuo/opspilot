"""Command execution and SSH terminal API endpoints for OpsPilot."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
import logging
import asyncio
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.server import Server
from app.models.organization import Organization, OrganizationMember

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# SSH Terminal State Management
# ============================================

# Active SSH sessions (in-memory storage)
# TODO: Move to Redis for production
active_ssh_sessions: Dict[str, Dict[str, Any]] = {}


class SSHSessionCreateRequest(BaseModel):
    """SSH session creation request schema."""

    server_id: str


class SSHSessionResponse(BaseModel):
    """SSH session response schema."""

    session_id: str
    server_id: str
    status: str


class CommandExecuteRequest(BaseModel):
    """Command execution request schema."""

    server_id: str
    command: str
    timeout_seconds: Optional[int] = 60


class CommandExecuteResponse(BaseModel):
    """Command execution response schema."""

    command_id: str
    server_id: str
    command: str
    status: str


# Response Schemas
class CommandResponse(BaseModel):
    """Command response schema."""

    id: str
    server_id: str
    command: str
    status: str
    output: Optional[str]
    error: Optional[str]
    exit_code: Optional[int]
    duration_seconds: Optional[int]
    created_at: str
    updated_at: str


class CommandsListResponse(BaseModel):
    """Commands list response schema."""

    total: int
    page: int
    page_size: int
    total_pages: int
    commands: List[CommandResponse]


# ============================================
# SSH Terminal Endpoints
# ============================================

@router.post("/servers/{server_id}/ssh/sessions", response_model=SSHSessionResponse)
async def create_ssh_session(
    server_id: str,
    request: SSHSessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new SSH session.

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

    # Verify server exists and user has access
    server_result = await db.execute(
        select(Server, OrganizationMember.organization_id)
        .join(OrganizationMember, Server.organization_id == OrganizationMember.organization_id)
        .where(
            Server.id == server_id,
            OrganizationMember.user_id == user_id
        )
    )
    server_data = server_result.fetchone()

    if not server_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found or no permission",
        )

    server, org_id = server_data

    # Check concurrent session limit
    # TODO: Implement with database
    active_count = len([
        s for s in active_ssh_sessions.values()
        if s["server_id"] == server_id and s["status"] == "active"
    ])

    if active_count >= 3:  # Default concurrent session limit
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Concurrent session limit reached",
        )

    # Create SSH session
    import uuid
    session_id = str(uuid.uuid4())

    active_ssh_sessions[session_id] = {
        "server_id": server.id,
        "organization_id": org_id,
        "user_id": user_id,
        "status": "created",
        "created_at": datetime.utcnow(),
        "ws_connection": None,
    }

    logger.info(f"SSH session created: {session_id} for server {server.id}")

    return SSHSessionResponse(
        session_id=session_id,
        server_id=server.id,
        status="created",
    )


@router.get("/ssh/sessions/{session_id}", response_model=SSHSessionResponse)
async def get_ssh_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get SSH session status.

    Args:
        session_id: Session ID
        current_user: Current authenticated user

    Returns:
        SSH session status

    Raises:
        HTTPException: If session not found or no permission
    """
    user_id = current_user["id"]

    if session_id not in active_ssh_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH session not found",
        )

    session = active_ssh_sessions[session_id]

    if session["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this session",
        )

    return SSHSessionResponse(
        session_id=session_id,
        server_id=session["server_id"],
        status=session["status"],
    )


@router.delete("/ssh/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_ssh_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Terminate an SSH session.

    Args:
        session_id: Session ID
        current_user: Current authenticated user

    Returns:
        204 No Content

    Raises:
        HTTPException: If session not found or no permission
    """
    user_id = current_user["id"]

    if session_id not in active_ssh_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH session not found",
        )

    session = active_ssh_sessions[session_id]

    if session["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to terminate this session",
        )

    # Close WebSocket connection if active
    if session["ws_connection"]:
        session["ws_connection"].close()

    # Remove from active sessions
    del active_ssh_sessions[session_id]

    logger.info(f"SSH session terminated: {session_id}")


@router.websocket("/ssh/ws/{session_id}")
async def ssh_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for SSH terminal I/O.

    Args:
        websocket: WebSocket connection
        session_id: SSH session ID
    """
    # Verify session exists
    if session_id not in active_ssh_sessions:
        logger.warning(f"SSH WebSocket connection rejected: session {session_id} not found")
        await websocket.close(code=4004, reason="Session not found")
        return

    session = active_ssh_sessions[session_id]

    # TODO: Verify user authentication via WebSocket query parameter
    # For now, accept connection

    # Accept WebSocket connection
    await websocket.accept()

    # Store WebSocket connection in session
    session["ws_connection"] = websocket
    session["status"] = "active"

    logger.info(f"SSH WebSocket connected: {session_id}")

    try:
        # TODO: Connect to server via SSH
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": f"Connected to server {session['server_id']}",
            "server_hostname": "server.example.com",  # TODO: Get from server record
        }))

        # Handle incoming messages (commands to execute)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "command":
                # Execute command and send output
                # TODO: Execute via SSH/Salt
                command = message["command"]
                output = f"Executed: {command}\n"

                await websocket.send_text(json.dumps({
                    "type": "output",
                    "output": output,
                    "timestamp": datetime.utcnow().isoformat(),
                }))

            elif message["type"] == "resize":
                # Handle terminal resize
                rows = message["rows"]
                cols = message["cols"]
                logger.info(f"Terminal resized: {rows}x{cols}")

            elif message["type"] == "close":
                # Client requested close
                break

    except WebSocketDisconnect:
        logger.info(f"SSH WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"SSH WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except:
            pass
    finally:
        # Update session status
        session["status"] = "closed"
        session["ws_connection"] = None
        if session_id in active_ssh_sessions:
            del active_ssh_sessions[session_id]


# ============================================
# Command Execution Endpoints
# ============================================

@router.post("/commands/execute", response_model=CommandExecuteResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_command(
    request: CommandExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Execute a command on a server.

    Args:
        request: Command execution request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Command execution response

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    # Verify server exists and user has access
    server_result = await db.execute(
        select(Server, OrganizationMember.organization_id)
        .join(OrganizationMember, Server.organization_id == OrganizationMember.organization_id)
        .where(
            Server.id == request.server_id,
            OrganizationMember.user_id == user_id
        )
    )
    server_data = server_result.fetchone()

    if not server_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found or no permission",
        )

    server, org_id = server_data

    # Create command record (TODO: Implement in database)
    import uuid
    command_id = str(uuid.uuid4())

    # TODO: Execute command via SSH/Salt
    logger.info(f"Command execution queued: {command_id} on server {server.id}: {request.command}")

    # Trigger command execution asynchronously
    # TODO: Use Celery or background tasks

    return CommandExecuteResponse(
        command_id=command_id,
        server_id=server.id,
        command=request.command,
        status="queued",
    )


@router.get("/commands/{command_id}", response_model=CommandResponse)
async def get_command(
    command_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get command by ID.

    Args:
        command_id: Command ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Command details

    Raises:
        HTTPException: If command not found or no permission
    """
    user_id = current_user["id"]

    # TODO: Implement in database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Command storage not yet implemented",
    )


@router.get("/commands", response_model=CommandsListResponse)
async def list_commands(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    server_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List command history.

    Args:
        page: Page number
        page_size: Items per page
        server_id: Filter by server
        status_filter: Filter by status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of commands
    """
    user_id = current_user["id"]

    # Get user's organizations
    org_result = await db.execute(
        select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id
        )
    )
    org_ids = [row[0] for row in org_result.fetchall()]

    # TODO: Implement commands table and list logic
    # For now, return empty list

    return CommandsListResponse(
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
        commands=[],
    )

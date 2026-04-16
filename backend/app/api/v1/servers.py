"""Server management API endpoints for OpsPilot."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.server import Server as ServerRow
from app.services.server_service import server_service
from app.services.background_agent_install import schedule_agent_install

router = APIRouter()


class ServerSshInstallCredentials(BaseModel):
    """SSH credentials for auto-install and for future OpsPilot-initiated SSH (password encrypted at rest)."""

    username: str
    password: str
    port: int = Field(default=22, ge=1, le=65535)


# Request Schemas
class ServerCreateRequest(BaseModel):
    """Server creation request schema."""

    hostname: str
    ip_address: str
    os_type: str
    domain_name: Optional[str] = None
    web_server_type: Optional[str] = None
    auto_install_agent: bool = False
    ssh: Optional[ServerSshInstallCredentials] = None

    @model_validator(mode="after")
    def _validate_auto_install(self) -> "ServerCreateRequest":
        if self.auto_install_agent:
            if self.os_type != "linux":
                raise ValueError("auto_install_agent is only supported when os_type is linux")
            if self.ssh is None:
                raise ValueError("ssh is required when auto_install_agent is true")
        return self


class ServerUpdateRequest(BaseModel):
    """Server update request schema."""

    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    domain_name: Optional[str] = None
    web_server_type: Optional[str] = None
    status: Optional[str] = None


class ApplyStateRequest(BaseModel):
    """Apply Salt state request schema."""

    state: str
    test: bool = False


# Response Schemas
class ServerResponse(BaseModel):
    """Server response schema."""

    id: str
    organization_id: str
    hostname: str
    ip_address: str
    os_type: str
    web_server_type: Optional[str]
    domain_name: Optional[str]
    status: str
    has_ssh_credentials: bool = False
    created_at: str
    updated_at: str


def server_row_to_response(server: ServerRow) -> ServerResponse:
    return ServerResponse(
        id=server.id,
        organization_id=server.organization_id,
        hostname=server.hostname,
        ip_address=server.ip_address,
        os_type=server.os_type,
        web_server_type=server.web_server_type,
        domain_name=server.domain_name,
        status=server.status,
        has_ssh_credentials=bool(server.ssh_username and server.ssh_password_encrypted),
        created_at=server.created_at.isoformat(),
        updated_at=server.updated_at.isoformat(),
    )


class ServersListResponse(BaseModel):
    """Servers list response schema."""

    total: int
    servers: List[ServerResponse]


class StateApplicationResponse(BaseModel):
    """State application response schema."""

    server_id: str
    state: str
    test: bool
    result: Dict[str, Any]


@router.post("/organizations/{organization_id}/servers", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    organization_id: str,
    request: ServerCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new server and set up Salt minion.

    Args:
        organization_id: Organization ID
        request: Server creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created server

    Raises:
        HTTPException: If server creation fails
    """
    user_id = current_user["id"]

    try:
        outcome = await server_service.create_server(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            hostname=request.hostname,
            ip_address=request.ip_address,
            os_type=request.os_type,
            domain_name=request.domain_name,
            web_server_type=request.web_server_type,
            auto_install_agent=request.auto_install_agent,
            ssh_username=request.ssh.username if request.ssh else None,
            ssh_password=request.ssh.password if request.ssh else None,
            ssh_port=request.ssh.port if request.ssh else 22,
        )
        server = outcome.server
        if outcome.auto_install:
            background_tasks.add_task(
                schedule_agent_install,
                server_id=server.id,
                organization_id=server.organization_id,
                ip_address=server.ip_address,
                agent_api_key=outcome.agent_api_key_plaintext,
                ssh_username=outcome.auto_install.username,
                ssh_password=outcome.auto_install.password,
                ssh_port=outcome.auto_install.port,
            )
        return server_row_to_response(server)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create server: {str(e)}",
        )


@router.get("/organizations/{organization_id}/servers", response_model=ServersListResponse)
async def list_servers(
    organization_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all servers in an organization.

    Args:
        organization_id: Organization ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of servers

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    try:
        servers = await server_service.list_servers(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
        return ServersListResponse(
            total=len(servers),
            servers=[server_row_to_response(server) for server in servers],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a server by ID.

    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Server details

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    server = await server_service.get_server(db, server_id, user_id)

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    return server_row_to_response(server)


@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: str,
    request: ServerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update a server.

    Args:
        server_id: Server ID
        request: Server update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated server

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    server = await server_service.update_server(
        db=db,
        server_id=server_id,
        user_id=user_id,
        updates=request.model_dump(exclude_unset=True),
    )

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    return server_row_to_response(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a server.

    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        204 No Content

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    success = await server_service.delete_server(db, server_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )


@router.post("/servers/{server_id}/states/apply", response_model=StateApplicationResponse)
async def apply_state(
    server_id: str,
    request: ApplyStateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Apply a Salt state to a server.

    Args:
        server_id: Server ID
        request: State application data
        db: Database session
        current_user: Current authenticated user

    Returns:
        State application result

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    try:
        result = await server_service.apply_salt_state(
            db=db,
            server_id=server_id,
            user_id=user_id,
            state=request.state,
            test=request.test,
        )
        return StateApplicationResponse(
            server_id=server_id,
            state=request.state,
            test=request.test,
            result=result,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

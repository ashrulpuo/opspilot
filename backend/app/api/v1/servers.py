"""Server management API endpoints for OpsPilot."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_keys import generate_agent_api_key, hash_agent_api_key
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.server import Server as ServerRow
from app.services.server_service import server_service
from app.services.background_agent_install import schedule_agent_install

router = APIRouter()


class ServerSshInstallCredentials(BaseModel):
    """SSH credentials for Salt minion auto-install and OpsPilot-initiated SSH (password encrypted at rest)."""

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
    agent_last_seen_at: Optional[str] = None
    agent_install_last_error: Optional[str] = None
    name: str
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    architecture: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    agent_reported_hostname: Optional[str] = None
    agent_reported_ip: Optional[str] = None


def server_row_to_response(server: ServerRow) -> ServerResponse:
    label = (server.display_name and server.display_name.strip()) or server.hostname
    os_name = server.agent_os_name
    os_version = server.agent_os_version
    if not os_name and server.os_type:
        os_name = server.os_type
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
        agent_last_seen_at=server.agent_last_seen_at.isoformat() if server.agent_last_seen_at else None,
        agent_install_last_error=server.agent_install_last_error,
        name=label,
        os_name=os_name,
        os_version=os_version,
        architecture=server.agent_architecture,
        cpu_cores=server.agent_cpu_cores,
        memory_mb=server.agent_memory_mb,
        agent_reported_hostname=server.agent_reported_hostname,
        agent_reported_ip=server.agent_reported_ip,
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
    """Create a new server, configure Salt pillar, and optionally SSH-install ``salt-minion``.

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

    if request.auto_install_agent:
        from app.core.config import get_settings

        if not (get_settings().SALT_MASTER_HOST or "").strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SALT_MASTER_HOST must be set on the API to auto-install the Salt minion",
            )

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


@router.post("/servers/{server_id}/reinstall-salt-minion", response_model=ServerResponse)
async def reinstall_salt_minion(
    server_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Queue another SSH Salt minion install using stored SSH credentials (Linux only)."""
    from app.core.config import get_settings

    if not (get_settings().SALT_MASTER_HOST or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SALT_MASTER_HOST must be set on the API to reinstall the Salt minion",
        )

    user_id = current_user["id"]
    creds = await server_service.get_decrypted_ssh_credentials(db, server_id, user_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server has no stored SSH credentials; add credentials or recreate the server with auto-install",
        )

    ssh_username, ssh_port, ssh_password = creds
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    if (server.os_type or "").lower() != "linux":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Salt minion reinstall is only supported for Linux servers",
        )

    # Fresh API key so the bundled push agent can be configured on the host (plaintext is never stored).
    agent_key_plain = generate_agent_api_key()
    server.agent_api_key_hash = hash_agent_api_key(agent_key_plain)
    server.status = "installing_agent"
    server.agent_install_last_error = None
    await db.commit()
    await db.refresh(server)

    background_tasks.add_task(
        schedule_agent_install,
        server_id=server.id,
        organization_id=server.organization_id,
        ip_address=server.ip_address,
        agent_api_key=agent_key_plain,
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        ssh_port=ssh_port,
    )
    return server_row_to_response(server)


@router.post("/servers/{server_id}/redeploy-agent", response_model=ServerResponse)
async def redeploy_push_agent(
    server_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Re-upload push agent script + config via SSH and restart its systemd service.

    Use after agent bundle updates. Does NOT reinstall Salt minion.
    """
    user_id = current_user["id"]
    creds = await server_service.get_decrypted_ssh_credentials(db, server_id, user_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server has no stored SSH credentials",
        )
    server = await server_service.get_server(db, server_id, user_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    ssh_username, ssh_port, ssh_password = creds

    agent_key_plain = generate_agent_api_key()
    server.agent_api_key_hash = hash_agent_api_key(agent_key_plain)
    await db.commit()
    await db.refresh(server)

    _org_id = server.organization_id
    _ip = server.ip_address

    async def _run() -> None:
        import asyncio as _aio
        from app.core.database import AsyncSessionLocal
        from app.services.agent_ssh_install import deploy_push_agent_only

        ok, err = await _aio.to_thread(
            deploy_push_agent_only,
            host=_ip,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            server_id=server_id,
            organization_id=_org_id,
            agent_api_key=agent_key_plain,
        )
        async with AsyncSessionLocal() as _db:
            from sqlalchemy import select as _sel
            r = await _db.execute(_sel(ServerRow).where(ServerRow.id == server_id))
            sv = r.scalar_one_or_none()
            if sv:
                sv.status = "online" if ok else "error"
                sv.agent_install_last_error = None if ok else (err or "redeploy failed")[:8000]
                await _db.commit()

    background_tasks.add_task(_run)
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

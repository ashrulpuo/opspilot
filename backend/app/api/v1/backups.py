"""Backup API endpoints for OpsPilot."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.server_service import server_service

router = APIRouter()


# Request Schemas
class BackupIngestRequest(BaseModel):
    """Backup report ingestion request schema."""

    server_id: str
    organization_id: str
    backup_results: Dict[str, Any]


class BackupIngestResponse(BaseModel):
    """Backup ingestion response schema."""

    message: str
    server_id: str


# Response Schemas
class BackupResponse(BaseModel):
    """Backup response schema."""

    server_id: str
    backup_result: Dict[str, Any]


class BackupHistoryResponse(BaseModel):
    """Backup history response schema."""

    server_id: str
    backups: list


@router.post("/servers/{server_id}/backups", response_model=BackupIngestResponse)
async def ingest_backup_report(
    server_id: str,
    request: BackupIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest backup report from OpsPilot agent (Salt minion).

    This endpoint is called by OpsPilot agents (via Salt) to send backup reports.
    The API key should be set in the Salt pillar and validated.

    Args:
        server_id: Server ID
        request: Backup report data
        db: Database session

    Returns:
        Confirmation message

    Raises:
        HTTPException: If server not found or invalid API key
    """
    # Validate server_id matches request
    if server_id != request.server_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server ID in URL does not match request body",
        )

    # TODO: Validate API key from request headers (X-API-Key)
    # For now, we skip API key validation for development

    # Validate server exists
    from app.models.server import Server
    from sqlalchemy import select

    result = await db.execute(
        select(Server).where(Server.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # TODO: Store backup report in database
    # backup_repo.store_backup_report(server_id, request.backup_results)

    return BackupIngestResponse(
        message="Backup report received successfully",
        server_id=server_id,
    )


@router.post("/servers/{server_id}/backups/execute", response_model=BackupResponse)
async def execute_backup(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Execute backup on a server.

    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup execution result

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    try:
        result = await server_service.execute_backup(db, server_id, user_id)
        return BackupResponse(server_id=server_id, backup_result=result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/servers/{server_id}/backups", response_model=BackupHistoryResponse)
async def get_server_backups(
    server_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get backup history for a server.

    Args:
        server_id: Server ID
        limit: Maximum number of backup records to retrieve (default: 10)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup history for server

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

    # TODO: Retrieve backup history from database
    # backups = backup_repo.get_backup_history(server_id, limit)

    return BackupHistoryResponse(
        server_id=server_id,
        backups=[],
    )


@router.get("/organizations/{organization_id}/backups/summary")
async def get_organization_backups_summary(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get backup summary for all servers in an organization.

    Args:
        organization_id: Organization ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup summary for organization

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    # TODO: Get all servers in organization and aggregate backups
    # servers = await server_service.list_servers(db, organization_id, user_id)

    return {
        "organization_id": organization_id,
        "message": "Backup summary not yet implemented",
    }


@router.get("/servers/{server_id}/backups/{backup_id}")
async def get_backup_details(
    server_id: str,
    backup_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get details of a specific backup.

    Args:
        server_id: Server ID
        backup_id: Backup ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup details

    Raises:
        HTTPException: If backup not found or no permission
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

    # TODO: Retrieve backup details from database
    # backup = backup_repo.get_backup_by_id(backup_id)

    return {
        "server_id": server_id,
        "backup_id": backup_id,
        "message": "Backup details not yet implemented",
    }


@router.post("/servers/{server_id}/backups/{backup_id}/restore")
async def restore_backup(
    server_id: str,
    backup_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Restore a backup to a server.

    Args:
        server_id: Server ID
        backup_id: Backup ID to restore
        db: Database session
        current_user: Current authenticated user

    Returns:
        Restore operation result

    Raises:
        HTTPException: If backup not found or no permission
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

    # TODO: Implement backup restore via Salt
    # result = await server_service.restore_backup(db, server_id, backup_id, user_id)

    return {
        "server_id": server_id,
        "backup_id": backup_id,
        "message": "Backup restore not yet implemented",
    }

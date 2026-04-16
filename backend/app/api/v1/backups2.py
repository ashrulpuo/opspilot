"""Backup management API endpoints for OpsPilot."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.server import Server
from app.models.organization import Organization, OrganizationMember

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Request Schemas
# ============================================

class CreateBackupScheduleRequest(BaseModel):
    """Backup schedule creation request schema."""

    server_id: str
    name: str
    source_paths: List[str]
    destination: str
    schedule_type: str  # "hourly", "daily", "weekly", "monthly"
    schedule_value: Optional[int] = None  # e.g., 2 for "every 2 hours"
    retention_days: int = 30
    enabled: bool = True
    compress: bool = False
    encrypt: bool = False
    description: Optional[str] = None


class UpdateBackupScheduleRequest(BaseModel):
    """Backup schedule update request schema."""

    name: Optional[str] = None
    source_paths: Optional[List[str]] = None
    destination: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_value: Optional[int] = None
    retention_days: Optional[int] = None
    enabled: Optional[bool] = None
    compress: Optional[bool] = None
    encrypt: Optional[bool] = None
    description: Optional[str] = None


class RunBackupRequest(BaseModel):
    """Run backup request schema."""

    server_id: str
    backup_schedule_id: Optional[str] = None  # If None, run ad-hoc backup


# ============================================
# Response Schemas
# ============================================

class BackupScheduleResponse(BaseModel):
    """Backup schedule response schema."""

    id: str
    server_id: str
    server_hostname: Optional[str]
    organization_id: str
    name: str
    source_paths: List[str]
    destination: str
    schedule_type: str
    schedule_value: Optional[int]
    retention_days: int
    enabled: bool
    compress: bool
    encrypt: bool
    description: Optional[str]
    created_at: str
    updated_at: str


class BackupHistoryResponse(BaseModel):
    """Backup history response schema."""

    id: str
    backup_schedule_id: Optional[str]
    schedule_name: Optional[str]
    server_id: str
    server_hostname: Optional[str]
    organization_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    files_transferred: Optional[int]
    bytes_transferred: Optional[int]
    checksum: Optional[str]
    error_message: Optional[str]


class BackupSchedulesListResponse(BaseModel):
    """Backup schedules list response schema."""

    total: int
    page: int
    page_size: int
    total_pages: int
    schedules: List[BackupScheduleResponse]


class BackupHistoryListResponse(BaseModel):
    """Backup history list response schema."""

    total: int
    page: int
    page_size: int
    total_pages: int
    backups: List[BackupHistoryResponse]


# ============================================
# Endpoints
# ============================================

@router.get("/organizations/{organization_id}/backup-schedules", response_model=BackupSchedulesListResponse)
async def list_backup_schedules(
    organization_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    server_id: Optional[str] = Query(None),
    enabled_only: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all backup schedules in an organization.

    Args:
        organization_id: Organization ID
        page: Page number
        page_size: Items per page
        server_id: Filter by server
        enabled_only: Filter by enabled status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of backup schedules

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this organization",
        )

    # Build query
    query = (
        select(CredentialsVaultPath, Server.hostname)
        .join(Server, CredentialsVaultPath.server_id == Server.id)
        .where(CredentialsVaultPath.organization_id == organization_id)
    )

    # Apply filters
    if server_id:
        query = query.where(CredentialsVaultPath.server_id == server_id)
    if enabled_only is not None:
        query = query.where(CredentialsVaultPath.enabled == enabled_only)

    # Order by created_at desc
    query = query.order_by(CredentialsVaultPath.created_at.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    results = await db.execute(query)
    schedules_with_hostnames = results.fetchall()

    # Build response (placeholder - TODO: Implement backup_schedules table)
    # For now, return empty list
    total_pages = (total + page_size - 1) // page_size

    return BackupSchedulesListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        schedules=[],
    )


@router.get("/backup-schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def get_backup_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a backup schedule by ID.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup schedule details

    Raises:
        HTTPException: If schedule not found or no permission
    """
    user_id = current_user["id"]

    # TODO: Implement backup_schedules table and get logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backup schedules table not yet implemented",
    )


@router.post("/organizations/{organization_id}/backup-schedules", response_model=BackupScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_schedule(
    organization_id: str,
    request: CreateBackupScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new backup schedule.

    Args:
        organization_id: Organization ID
        request: Backup schedule creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created backup schedule

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this organization",
        )

    # Verify server exists and belongs to organization
    server_result = await db.execute(
        select(Server).where(
            Server.id == request.server_id,
            Server.organization_id == organization_id
        )
    )
    server = server_result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    # TODO: Implement backup_schedules table and create logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backup schedules table not yet implemented",
    )


@router.put("/backup-schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def update_backup_schedule(
    schedule_id: str,
    request: UpdateBackupScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update a backup schedule.

    Args:
        schedule_id: Schedule ID
        request: Backup schedule update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated backup schedule

    Raises:
        HTTPException: If schedule not found or no permission
    """
    user_id = current_user["id"]

    # TODO: Implement backup_schedules table and update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backup schedules table not yet implemented",
    )


@router.delete("/backup-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a backup schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        204 No Content

    Raises:
        HTTPException: If schedule not found or no permission
    """
    user_id = current_user["id"]

    # TODO: Implement backup_schedules table and delete logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backup schedules table not yet implemented",
    )


@router.post("/backups/run", status_code=status.HTTP_202_ACCEPTED)
async def run_backup(
    request: RunBackupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Run a backup immediately (ad-hoc or scheduled).

    Args:
        request: Backup execution request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Accepted response

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

    # TODO: Trigger Salt runner to execute backup
    # Send request to Salt minion to execute backup
    logger.info(f"Backup triggered for server {server.id}: ad-hoc={request.backup_schedule_id is None}")

    return {"message": "Backup started", "server_id": server.id}


@router.get("/organizations/{organization_id}/backup-history", response_model=BackupHistoryListResponse)
async def list_backup_history(
    organization_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    server_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List backup history.

    Args:
        organization_id: Organization ID
        page: Page number
        page_size: Items per page
        server_id: Filter by server
        status_filter: Filter by status
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of backup history

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    # Verify user has access to organization
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        )
    )
    org_member = org_member_result.scalar_one_or_none()

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this organization",
        )

    # TODO: Implement backup_reports table and list logic
    # For now, return empty list
    total_pages = 0

    return BackupHistoryListResponse(
        total=0,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        backups=[],
    )


@router.get("/backups/{backup_id}", response_model=BackupHistoryResponse)
async def get_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a backup by ID.

    Args:
        backup_id: Backup ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Backup details

    Raises:
        HTTPException: If backup not found or no permission
    """
    user_id = current_user["id"]

    # TODO: Implement backup_reports table and get logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backup reports table not yet implemented",
    )

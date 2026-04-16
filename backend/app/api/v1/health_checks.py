"""Health check API endpoints for OpsPilot."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.server_service import server_service

router = APIRouter()


# Request Schemas
class HealthIngestRequest(BaseModel):
    """Health check report ingestion request schema."""

    server_id: str
    organization_id: str
    checks: Dict[str, Any]


class HealthIngestResponse(BaseModel):
    """Health check ingestion response schema."""

    message: str
    server_id: str


# Response Schemas
class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    server_id: str
    overall_status: str
    checks: Dict[str, Any]


@router.post("/servers/{server_id}/health", response_model=HealthIngestResponse)
async def ingest_health_report(
    server_id: str,
    request: HealthIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest health check report from OpsPilot agent (Salt minion).

    This endpoint is called by OpsPilot agents (via Salt) to send health reports.
    The API key should be set in the Salt pillar and validated.

    Args:
        server_id: Server ID
        request: Health check data
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

    # Update server status based on health
    overall_status = request.checks.get("overall_status", "unknown")
    if overall_status == "healthy":
        server.status = "active"
    elif overall_status == "warning":
        server.status = "warning"
    else:
        server.status = "error"

    await db.commit()

    # TODO: Store health report in database
    # health_repo.store_health_report(server_id, request.checks)

    return HealthIngestResponse(
        message="Health report received successfully",
        server_id=server_id,
    )


@router.post("/servers/{server_id}/health/check", response_model=HealthCheckResponse)
async def perform_health_check(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Perform health check on a server.

    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Health check result

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    try:
        result = await server_service.health_check(db, server_id, user_id)
        overall_status = result.get("overall_status", "unknown")

        # Update server status
        from app.models.server import Server
        from sqlalchemy import select

        server_result = await db.execute(
            select(Server).where(Server.id == server_id)
        )
        server = server_result.scalar_one_or_none()

        if server:
            if overall_status == "healthy":
                server.status = "active"
            elif overall_status == "warning":
                server.status = "warning"
            else:
                server.status = "error"
            await db.commit()

        return HealthCheckResponse(
            server_id=server_id,
            overall_status=overall_status,
            checks=result.get("checks", {}),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/servers/{server_id}/health/history")
async def get_server_health_history(
    server_id: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get health check history for a server.

    Args:
        server_id: Server ID
        hours: Number of hours of history to retrieve (default: 24)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Health check history for server

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

    # TODO: Retrieve health check history from database
    # health_history = health_repo.get_health_history(server_id, hours)

    return {
        "server_id": server_id,
        "hours": hours,
        "message": "Health check history not yet implemented",
    }


@router.get("/organizations/{organization_id}/health/summary")
async def get_organization_health_summary(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get health summary for all servers in an organization.

    Args:
        organization_id: Organization ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Health summary for organization

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    # TODO: Get all servers in organization and aggregate health status
    # servers = await server_service.list_servers(db, organization_id, user_id)
    # health_summary = health_repo.get_organization_health_summary(organization_id)

    return {
        "organization_id": organization_id,
        "message": "Health summary not yet implemented",
    }

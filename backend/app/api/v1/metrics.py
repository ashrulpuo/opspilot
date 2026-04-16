"""Metrics API endpoints for OpsPilot."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.server_service import server_service

router = APIRouter()


# Request Schemas
class MetricsIngestRequest(BaseModel):
    """Metrics ingestion request schema."""

    server_id: str
    organization_id: str
    metrics: Dict[str, Any]


class MetricsIngestResponse(BaseModel):
    """Metrics ingestion response schema."""

    message: str
    server_id: str


# Response Schemas
class MetricsResponse(BaseModel):
    """Metrics response schema."""

    server_id: str
    metrics: Dict[str, Any]


@router.post("/servers/{server_id}/metrics", response_model=MetricsIngestResponse)
async def ingest_metrics(
    server_id: str,
    request: MetricsIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest metrics from OpsPilot agent (Salt minion).

    This endpoint is called by OpsPilot agents (via Salt) to send metrics.
    The API key should be set in the Salt pillar and validated.

    Args:
        server_id: Server ID
        request: Metrics data
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

    # TODO: Store metrics in database (TimescaleDB hypertable)
    # We'll implement this in the metrics repository

    # Log metrics
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

    # TODO: Store metrics in TimescaleDB
    # metrics_repo.store_metrics(server_id, request.metrics)

    return MetricsIngestResponse(
        message="Metrics received successfully",
        server_id=server_id,
    )


@router.get("/servers/{server_id}/metrics", response_model=MetricsResponse)
async def get_server_metrics(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get latest metrics for a server.

    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Latest metrics for server

    Raises:
        HTTPException: If server not found or no permission
    """
    user_id = current_user["id"]

    try:
        metrics = await server_service.collect_metrics(db, server_id, user_id)
        return MetricsResponse(server_id=server_id, metrics=metrics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/servers/{server_id}/metrics/history")
async def get_server_metrics_history(
    server_id: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get historical metrics for a server.

    Args:
        server_id: Server ID
        hours: Number of hours of history to retrieve (default: 24)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Historical metrics for server

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

    # TODO: Retrieve historical metrics from TimescaleDB
    # metrics_history = metrics_repo.get_metrics_history(server_id, hours)

    return {
        "server_id": server_id,
        "hours": hours,
        "message": "Historical metrics retrieval not yet implemented",
        # "metrics": metrics_history
    }


@router.get("/organizations/{organization_id}/metrics/summary")
async def get_organization_metrics_summary(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get metrics summary for all servers in an organization.

    Args:
        organization_id: Organization ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Metrics summary for organization

    Raises:
        HTTPException: If no permission to access organization
    """
    user_id = current_user["id"]

    # TODO: Get all servers in organization and aggregate metrics
    # servers = await server_service.list_servers(db, organization_id, user_id)

    return {
        "organization_id": organization_id,
        "message": "Metrics summary not yet implemented",
    }

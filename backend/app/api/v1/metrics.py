"""Metrics API endpoints for OpsPilot."""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.agent_keys import verify_agent_api_key
from app.models.server import Server
from app.services.server_service import server_service
from app.services import metrics_push_service

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
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Ingest metrics from OpsPilot host agent (push). Requires per-server X-API-Key."""
    if server_id != request.server_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server ID in URL does not match request body",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )

    if not server.agent_api_key_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server has no agent API key registered",
        )

    if not verify_agent_api_key(x_api_key, server.agent_api_key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if server.organization_id != request.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id does not match this server",
        )

    await metrics_push_service.insert_push_sample(db, server_id=server_id, payload=request.metrics)
    await metrics_push_service.mark_agent_seen(db, server)
    await db.commit()

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
    """Get latest metrics for a server (prefers fresh push-agent samples, else Salt)."""
    user_id = current_user["id"]

    try:
        metrics = await server_service.get_metrics_for_dashboard(db, server_id, user_id)
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
    """Get historical metrics for a server."""
    user_id = current_user["id"]

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

    return {
        "server_id": server_id,
        "hours": hours,
        "message": "Historical metrics retrieval not yet implemented",
    }


@router.get("/organizations/{organization_id}/metrics/summary")
async def get_organization_metrics_summary(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get metrics summary for all servers in an organization."""
    user_id = current_user["id"]

    return {
        "organization_id": organization_id,
        "message": "Metrics summary not yet implemented",
    }

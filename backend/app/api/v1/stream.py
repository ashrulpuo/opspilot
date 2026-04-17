"""SSE endpoints for real-time updates with JWT authentication."""
from fastapi import APIRouter, Depends, Header, Query, HTTPException, status
from fastapi.responses import StreamingResponse
import logging
from typing import Optional

from app.services.sse_service import SSEService
from app.core.security import verify_token
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stream", tags=["SSE"])

# Initialize SSE service with Redis URL
sse_service = SSEService(redis_url=settings.redis_url)


async def _get_token_from_header(authorization: str) -> str:
    """Extract Bearer token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        JWT token (without 'Bearer ' prefix)
        
    Raises:
        HTTPException if header is missing or invalid format
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )
    
    token = authorization.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token is empty"
        )
    
    return token


@router.get("/metrics")
async def stream_metrics(
    server_id: Optional[str] = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream real-time metrics via SSE with JWT auth.
    
    Query params:
        server_id: Stream specific server (optional, default: all servers)
    
    Headers:
        Authorization: JWT Bearer token (required)
        
    Returns:
        SSE stream of metric events
        
    Message format:
        event: metric
        data: {
          "server_id": "...",
          "metric_name": "cpu_percent",
          "metric_value": 45.2,
          "unit": "%",
          "timestamp": "2026-04-17T14:00:00Z"
        }
        
    Channel naming:
        - If server_id provided: `metrics:{server_id}`
        - If no server_id: `metrics:all` (admin only)
    """
    try:
        # Verify and extract JWT token
        token = await _get_token_from_header(authorization)
        
        # Build channel name
        if server_id:
            channel = f"metrics:{server_id}"
        else:
            # Require server_id for non-admin users
            # For now, allow `all` channel
            channel = "metrics:all"
        
        logger.info(f"Starting SSE metrics stream for channel: {channel}")
        
        return StreamingResponse(
            sse_service.subscribe_and_stream(channel, token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in metrics stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/alerts")
async def stream_alerts(
    server_id: Optional[str] = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream alerts via SSE with JWT auth.
    
    Query params:
        server_id: Stream specific server (optional, default: all)
    
    Headers:
        Authorization: JWT Bearer token (required)
        
    Returns:
        SSE stream of alert events
        
    Message format:
        event: alert
        data: {
          "server_id": "...",
          "alert_type": "cpu_high",
          "severity": "critical",
          "message": "CPU usage 95.2% > 90%",
          "timestamp": "2026-04-17T14:00:00Z"
        }
        
    Channel naming:
        - If server_id provided: `alerts:{server_id}`
        - If no server_id: `alerts:all` (admin only)
    """
    try:
        token = await _get_token_from_header(authorization)
        
        if server_id:
            channel = f"alerts:{server_id}"
        else:
            channel = "alerts:all"
        
        logger.info(f"Starting SSE alerts stream for channel: {channel}")
        
        return StreamingResponse(
            sse_service.subscribe_and_stream(channel, token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in alerts stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/services")
async def stream_services(
    server_id: Optional[str] = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream service state changes via SSE with JWT auth.
    
    Query params:
        server_id: Stream specific server (optional, default: all)
    
    Headers:
        Authorization: JWT Bearer token (required)
        
    Returns:
        SSE stream of service state events
        
    Message format:
        event: service_state
        data: {
          "server_id": "...",
          "service_name": "nginx",
          "status": "running",
          "previous_status": "stopped",
          "timestamp": "2026-04-17T14:00:00Z"
        }
        
    Channel naming:
        - If server_id provided: `services:{server_id}`
        - If no server_id: `services:all`
    """
    try:
        token = await _get_token_from_header(authorization)
        
        if server_id:
            channel = f"services:{server_id}"
        else:
            channel = "services:all"
        
        logger.info(f"Starting SSE services stream for channel: {channel}")
        
        return StreamingResponse(
            sse_service.subscribe_and_stream(channel, token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in services stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/processes")
async def stream_processes(
    server_id: Optional[str] = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream process list via SSE with JWT auth (NEW).
    
    Query params:
        server_id: Stream specific server (optional, default: all)
        
    Returns:
        SSE stream of process list events
        
    Message format:
        event: process_list
        data: {
          "server_id": "...",
          "processes": [
            {"pid": 1234, "name": "nginx", "cpu_percent": 2.5, "memory_percent": 5.2, "state": "S"},
            ]
        }
        
    Channel naming:
        - If server_id provided: `processes:{server_id}`
        - If no server_id: `processes:all` (admin only)
    """
    try:
        token = await _get_token_from_header(authorization)
        
        if server_id:
            channel = f"processes:{server_id}"
        else:
            channel = "processes:all"
        
        logger.info(f"Starting SSE processes stream for channel: {channel}")
        
        return StreamingResponse(
            sse_service.subscribe_and_stream(channel, token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in processes stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/packages")
async def stream_packages(
    server_id: Optional[str] = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream package updates via SSE with JWT auth (NEW).
    
    Query params:
        server_id: Stream specific server (optional, default: all)
        
    Returns:
        SSE stream of package update events
        
    Message format:
        event: package_update
        data: {
          "server_id": "...",
          "packages": [
            {"name": "nginx", "version": "1.24.0", "is_update_available": True, "update_version": "1.24.1"},
          ]
        }
        
    Channel naming:
        - If server_id provided: `packages:{server_id}`
        - If no server_id: `packages:all` (admin only)
    """
    try:
        token = await _get_token_from_header(authorization)
        
        if server_id:
            channel = f"packages:{server_id}"
        else:
            channel = "packages:all"
        
        logger.info(f"Starting SSE packages stream for channel: {channel}")
        
        return StreamingResponse(
            sse_service.subscribe_and_stream(channel, token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in packages stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/logs")
async def stream_logs(
    server_id: Optional[str] = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream log entries via SSE with JWT auth (NEW).
    
    Query params:
        server_id: Stream specific server (optional, default: all)
        
    Returns:
        SSE stream of log entry events
        
    Message format:
        event: log_entry
        data: {
          "server_id": "...",
          "log": {
            "timestamp": "2026-04-17T14:00:00Z",
            "log_level": "INFO",
            "source": "nginx",
            "message": "GET /api/v1/users 200 OK"
          }
        }
        
    Channel naming:
        - If server_id provided: `logs:{server_id}`
        - If no server_id: `logs:all` (admin only)
    """
    try:
        token = await _get_token_from_header(authorization)
        
        if server_id:
            channel = f"logs:{server_id}"
        else:
            channel = "logs:all"
        
        logger.info(f"Starting SSE logs stream for channel: {channel}")
        
        return StreamingResponse(
            sse_service.subscribe_and_stream(channel, token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in logs stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# Health check endpoint for SSE service
@router.get("/health")
async def sse_health():
    """
    Health check endpoint for SSE service.
    
    Returns:
        Status of SSE service components
    """
    try:
        import redis.asyncio as redis
        
        # Check Redis connection
        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        redis_health = await r.ping()
        await r.close()
        
        return {
            "status": "healthy",
            "redis_connected": redis_health,
            "service": "SSE streaming",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"SSE health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "SSE streaming",
            "timestamp": datetime.utcnow().isoformat()
        }

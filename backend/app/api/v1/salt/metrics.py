"""Salt metrics ingestion endpoint (EXPANDED - includes processes, packages, logs)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.services.salt_api_client import SaltAPIClient
from app.core.security import verify_salt_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/salt", tags=["Salt Ingestion"])

# Initialize Salt API client
salt_api_client = SaltAPIClient()


# ============================================
# Request Schemas
# ============================================

class MetricsPayload(BaseModel):
    """Metrics payload from minion (EXPANDED)."""
    minion_id: str = Field(..., description="Salt minion ID")
    server_id: str = Field(..., description="OpsPilot server ID")
    timestamp: str = Field(..., description="UTC timestamp in ISO format")
    
    # Core metrics
    cpu_stats: Optional[Dict[str, Any]] = Field(None, description="CPU stats (status.cpustats)")
    mem_info: Optional[Dict[str, Any]] = Field(None, description="Memory info (status.meminfo)")
    disk_usage: Optional[Dict[str, Any]] = Field(None, description="Disk usage (status.diskusage)")
    disk_stats: Optional[Dict[str, Any]] = Field(None, description="Disk I/O (status.diskstats)")
    net_dev: Optional[Dict[str, Any]] = Field(None, description="Network devices (status.netdev)")
    net_stats: Optional[Dict[str, Any]] = Field(None, description="Network stats (status.netstats)")
    load_avg: Optional[Dict[str, Any]] = Field(None, description="Load averages (status.loadavg)")
    
    # EXPANDED metrics
    processes: Optional[List[Dict[str, Any]]] = Field(None, description="Process list (status.procs)")
    packages: Optional[List[Dict[str, Any]]] = Field(None, description="Package list (pkg.list_pkgs)")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="Log entries (from cmd.run)")
    
    class Config:
        schema_extra = {
            "example": {
                "minion_id": "web01",
                "server_id": "server-123",
                "timestamp": "2026-04-17T14:00:00Z",
                "cpu_stats": {
                    "cpu0": {"user": 15.2, "system": 5.3}
                },
                "mem_info": {
                    "MemTotal": 16777216,
                    "MemAvailable": 10485760
                },
                "processes": [
                    {"pid": 1234, "name": "nginx", "cpu_percent": 2.5}
                ],
                "packages": [
                    {"name": "nginx", "version": "1.24.0", "is_update_available": True}
                ],
                "logs": [
                    {"timestamp": "2026-04-17T14:00:00Z", "level": "INFO", "message": "Started"}
                ]
            }
        }


class BeaconEventPayload(BaseModel):
    """Beacon event payload from minion."""
    minion_id: str = Field(..., description="Salt minion ID")
    server_id: str = Field(..., description="OpsPilot server ID")
    timestamp: str = Field(..., description="UTC timestamp in ISO format")
    beacon_type: str = Field(..., description="Beacon type: cpu_alert, memory_alert, disk_alert, service_alert")
    beacon_data: Dict[str, Any] = Field(..., description="Beacon event data (thresholds, values, etc.)")


class ServiceStatePayload(BaseModel):
    """Service state payload from minion."""
    minion_id: str = Field(..., description="Salt minion ID")
    server_id: str = Field(..., description="OpsPilot server ID")
    timestamp: str = Field(..., description="UTC timestamp in ISO format")
    services: Dict[str, str] = Field(..., description="Service states")


# ============================================
# Response Schemas
# ============================================

class SuccessResponse(BaseModel):
    """Success response schema."""
    status: str
    detail: Optional[str] = None


class CountResponse(BaseModel):
    """Count response schema."""
    status: str
    count: int


# ============================================
# Endpoints
# ============================================

@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED, response_model=CountResponse)
async def ingest_metrics(
    payload: MetricsPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest metrics from Salt minion (EXPANDED).
    
    Expected metrics structure:
    - cpu_stats: status.cpustats (per-core data)
    - mem_info: status.meminfo
    - disk_usage: status.diskusage
    - disk_stats: status.diskstats (I/O data)
    - net_dev: status.netdev
    - net_stats: status.netstats (TCP/UDP connections)
    - load_avg: status.loadavg
    - processes: status.procs (EXPANDED - full list)
    - packages: pkg.list_pkgs (EXPANDED - full list)
    - logs: Log entries (EXPANDED - from cmd.run)
    
    All data is parsed and stored in database.
    Redis pub/sub publishes events for SSE streaming.
    """
    try:
        # Build metrics data dictionary
        metrics_data = {}
        
        if payload.cpu_stats:
            metrics_data["cpu_stats"] = payload.cpu_stats
        
        if payload.mem_info:
            metrics_data["mem_info"] = payload.mem_info
        
        if payload.disk_usage:
            metrics_data["disk_usage"] = payload.disk_usage
        
        if payload.disk_stats:
            metrics_data["disk_stats"] = payload.disk_stats
        
        if payload.net_dev:
            metrics_data["net_dev"] = payload.net_dev
        
        if payload.net_stats:
            metrics_data["net_stats"] = payload.net_stats
        
        if payload.load_avg:
            metrics_data["load_avg"] = payload.load_avg
        
        if payload.processes:
            metrics_data["processes"] = payload.processes
        
        if payload.packages:
            metrics_data["packages"] = payload.packages
        
        if payload.logs:
            metrics_data["logs"] = payload.logs
        
        # Ingest metrics
        metrics = await salt_api_client.ingest_metrics(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            metrics_data=metrics_data
        )
        
        logger.info(f"Ingested {len(metrics)} metrics from minion {payload.minion_id}")
        return CountResponse(status="accepted", count=len(metrics))
        
    except Exception as e:
        logger.error(f"Failed to ingest metrics from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest metrics: {str(e)}"
        )


@router.post("/beacon", status_code=status.HTTP_202_ACCEPTED, response_model=SuccessResponse)
async def ingest_beacon_event(
    payload: BeaconEventPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest beacon event (alert).
    
    Beacon types:
    - cpu_alert: CPU usage exceeded threshold
    - memory_alert: Memory usage exceeded threshold
    - disk_alert: Disk usage exceeded threshold
    - service_alert: Service state changed
    
    Beacons are processed and stored as events. Alerts are published to Redis for SSE streaming.
    """
    try:
        # Store beacon event
        event = await salt_api_client.ingest_beacon_event(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            event_tag=f"salt/beacon/{payload.beacon_type}/",
            event_type=payload.beacon_type,
            event_data=payload.beacon_data
        )
        
        logger.info(f"Beacon event {payload.beacon_type} from minion {payload.minion_id}")
        return SuccessResponse(status="accepted")
        
    except Exception as e:
        logger.error(f"Failed to ingest beacon event from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest beacon event: {str(e)}"
        )


@router.post("/services", status_code=status.HTTP_202_ACCEPTED, response_model=CountResponse)
async def ingest_service_states(
    payload: ServiceStatePayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest service states from Salt minion.
    
    Expected services structure:
    {
      "nginx": "running",
      "mysql": "stopped",
      "redis": "running"
    }
    
    Each service state is updated and changes are published to Redis for SSE streaming.
    """
    try:
        count = 0
        
        for service_name, service_status in payload.services.items():
            await salt_api_client.update_service_state(
                minion_id=payload.minion_id,
                server_id=payload.server_id,
                service_name=service_name,
                status=service_status
            )
            count += 1
        
        logger.info(f"Ingested {count} service states from minion {payload.minion_id}")
        return CountResponse(status="accepted", count=count)
        
    except Exception as e:
        logger.error(f"Failed to ingest service states from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest service states: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def salt_ingestion_health():
    """Health check endpoint for Salt ingestion API."""
    return {
        "status": "healthy",
        "service": "Salt Ingestion",
        "version": "1.0.0",
        "endpoints": [
            "/salt/heartbeat",
            "/salt/metrics",
            "/salt/beacon",
            "/salt/services"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

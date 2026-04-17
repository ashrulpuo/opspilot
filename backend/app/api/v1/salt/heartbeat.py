"""Salt ingestion API v1 router."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.services.salt_api_client import SaltAPIClient
from app.core.security import verify_salt_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/salt", tags=["Salt Ingestion"])

# Initialize Salt API client
salt_api_client = SaltAPIClient()


# ============================================
# Request Schemas
# ============================================

class MinionHeartbeat(BaseModel):
    """Minion heartbeat schema."""
    minion_id: str = Field(..., description="Salt minion ID")
    server_id: str = Field(..., description="OpsPilot server ID")
    timestamp: str = Field(..., description="UTC timestamp in ISO format")
    grains: Optional[Dict[str, Any]] = Field(None, description="Grains data (optional, only on first heartbeat)")


class MetricsPayload(BaseModel):
    """Metrics payload from minion."""
    minion_id: str
    server_id: str
    timestamp: str
    metrics: Dict[str, Any] = Field(
        ...,
        description="Raw metrics from Salt status modules",
        example={
            "cpu_stats": {"cpu0": {"user": 15.2, "system": 5.3}},
            "mem_info": {"MemTotal": 16777216, "MemAvailable": 10485760},
            "disk_usage": {"/": {"total": 536870912000000, "used": 322122547200000, "percent": 63.1}},
            "net_dev": {"eth0": {"rx_bytes": 12582912000, "tx_bytes": 6291456000}},
            "load_avg": {"1-min": 2.34, "5-min": 2.12, "15-min": 2.98},
            "processes": [{"pid": 1234, "name": "nginx", "cpu_percent": 2.5}],
            "packages": [{"name": "nginx", "version": "1.24.0", "is_update_available": True}],
            "logs": [{"timestamp": "2026-04-17T14:00:00Z", "level": "INFO", "source": "nginx", "message": "Started"}]
        }
    )


class BeaconEventPayload(BaseModel):
    """Beacon event payload from minion."""
    minion_id: str
    server_id: str
    timestamp: str
    beacon_type: str  # 'cpu_alert', 'memory_alert', 'disk_alert', 'service_alert'
    beacon_data: Dict[str, Any] = Field(
        ...,
        description="Beacon event data (thresholds, values, etc.)",
        example={
            "threshold": 90,
            "current_value": 95.2,
            "message": "CPU usage > 90%"
        }
    )


class ServiceStatePayload(BaseModel):
    """Service state payload from minion."""
    minion_id: str
    server_id: str
    timestamp: str
    services: Dict[str, str] = Field(
        ...,
        description="Service states",
        example={
            "nginx": "running",
            "mysql": "stopped",
            "redis": "running"
        }
    )


class ProcessListPayload(BaseModel):
    """Process list payload from minion (NEW)."""
    minion_id: str
    server_id: str
    timestamp: str
    processes: List[Dict[str, Any]] = Field(
        ...,
        description="Process list",
        example=[
            {
                "pid": 1234,
                "name": "nginx",
                "username": "www-data",
                "cpu_percent": 2.5,
                "memory_percent": 5.2,
                "state": "S",
                "command": "nginx: worker process"
            }
        ]
    )


class PackageListPayload(BaseModel):
    """Package list payload from minion (NEW)."""
    minion_id: str
    server_id: str
    timestamp: str
    packages: List[Dict[str, Any]] = Field(
        ...,
        description="Package list",
        example=[
            {
                "name": "nginx",
                "version": "1.24.0",
                "architecture": "amd64",
                "source": "apt",
                "is_update_available": True,
                "installed_date": "2026-04-17T14:00:00Z"
            }
        ]
    )


class LogEntriesPayload(BaseModel):
    """Log entries payload from minion (NEW)."""
    minion_id: str
    server_id: str
    timestamp: str
    logs: List[Dict[str, Any]] = Field(
        ...,
        description="Log entries",
        example=[
            {
                "timestamp": "2026-04-17T14:00:00Z",
                "level": "INFO",
                "source": "nginx",
                "message": "Started",
                "metadata": {"client_ip": "192.168.1.100", "request_id": "12345"}
            }
        ]
    )


# ============================================
# Response Schemas
# ============================================

class SuccessResponse(BaseModel):
    """Success response schema."""
    status: str = "accepted"
    detail: Optional[str] = None


class CountResponse(BaseModel):
    """Count response schema."""
    status: str
    count: int


# ============================================
# Endpoints
# ============================================

@router.post("/heartbeat", status_code=status.HTTP_202_ACCEPTED, response_model=SuccessResponse)
async def minion_heartbeat(
    payload: MinionHeartbeat,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Receive heartbeat from Salt minion.
    
    This updates minion's last_seen timestamp.
    If grains are provided, updates os_info and grains_info.
    
    Args:
        payload: Minion heartbeat data
        api_key: Salt API key for verification
        
    Returns:
        Success response
    """
    try:
        # Extract OS info from grains
        os_info = {
            "os": payload.grains.get("os") if payload.grains else None,
            "osfullname": payload.grains.get("osfullname") if payload.grains else None,
            "osrelease": payload.grains.get("osrelease") if payload.grains else None,
            "osfamily": payload.grains.get("osfamily") if payload.grains else None,
            "osarch": payload.grains.get("osarch") if payload.grains else None,
            "kernel": payload.grains.get("kernel") if payload.grains else None,
            "hostname": payload.grains.get("hostname") if payload.grains else None,
            "fqdn": payload.grains.get("fqdn") if payload.grains else None,
        }
        
        # Register/update minion
        minion = await salt_api_client.register_minion(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            grains=payload.grains or {},
            os_info=os_info
        )
        
        logger.info(f"Heartbeat from minion {payload.minion_id} (server {payload.server_id})")
        return SuccessResponse(status="accepted")
        
    except Exception as e:
        logger.error(f"Failed to process heartbeat from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process heartbeat: {str(e)}"
        )


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED, response_model=CountResponse)
async def ingest_metrics(
    payload: MetricsPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest metrics from Salt minion.
    
    Expected metrics structure:
    - cpu_stats: status.cpustats (per-core data)
    - mem_info: status.meminfo
    - disk_usage: status.diskusage
    - disk_stats: status.diskstats (I/O data)
    - net_dev: status.netdev
    - net_stats: status.netstats (TCP/UDP connections)
    - load_avg: status.loadavg
    - processes: status.procs (process list)
    - packages: pkg.list_pkgs (package list)
    - logs: log entries (from cmd.run collecting logs)
    
    All metrics are stored in database and published to Redis for SSE streaming.
    """
    try:
        # Ingest metrics
        metrics = await salt_api_client.ingest_metrics(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            metrics_data=payload.metrics
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
    
    Beacons are processed and stored as events. Alerts are published to Redis for SSE.
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
    
    Each service state is updated and changes are published to Redis for SSE.
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


@router.post("/processes", status_code=status.HTTP_202_ACCEPTED, response_model=CountResponse)
async def ingest_processes(
    payload: ProcessListPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest process list from Salt minion (NEW).
    
    Process structure per entry:
    {
      "pid": 1234,
      "name": "nginx",
      "username": "www-data",
      "cpu_percent": 2.5,
      "memory_percent": 5.2,
      "state": "S",
      "command": "nginx: worker process",
      "start_time": "2026-04-17T14:00:00Z"
    }
    
    All processes are stored in database and published to Redis for SSE streaming.
    """
    try:
        # Ingest processes (this is part of the metrics ingestion)
        # The salt_api_client already handles processes in ingest_metrics()
        # This endpoint is for explicit process list ingestion
        
        # For now, we'll include it in the metrics payload
        # If you want a dedicated endpoint, we can implement it
        
        # TODO: Implement dedicated process ingestion if needed
        # For now, pass through to metrics ingestion
        metrics_data = {"processes": payload.processes}
        
        await salt_api_client.ingest_metrics(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            metrics_data=metrics_data
        )
        
        logger.info(f"Ingested {len(payload.processes)} processes from minion {payload.minion_id}")
        return CountResponse(status="accepted", count=len(payload.processes))
        
    except Exception as e:
        logger.error(f"Failed to ingest processes from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest processes: {str(e)}"
        )


@router.post("/packages", status_code=status.HTTP_202_ACCEPTED, response_model=CountResponse)
async def ingest_packages(
    payload: PackageListPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest package list from Salt minion (NEW).
    
    Package structure per entry:
    {
      "name": "nginx",
      "version": "1.24.0",
      "architecture": "amd64",
      "source": "apt",
      "is_update_available": True,
      "installed_date": "2026-04-17T14:00:00Z",
      "update_version": "1.24.1" (if available)
    }
    
    All packages are stored in database and published to Redis for SSE streaming.
    """
    try:
        # Ingest packages (this is part of the metrics ingestion)
        # The salt_api_client already handles packages in ingest_metrics()
        # This endpoint is for explicit package list ingestion
        
        # TODO: Implement dedicated package ingestion if needed
        # For now, pass through to metrics ingestion
        metrics_data = {"packages": payload.packages}
        
        await salt_api_client.ingest_metrics(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            metrics_data=metrics_data
        )
        
        logger.info(f"Ingested {len(payload.packages)} packages from minion {payload.minion_id}")
        return CountResponse(status="accepted", count=len(payload.packages))
        
    except Exception as e:
        logger.error(f"Failed to ingest packages from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest packages: {str(e)}"
        )


@router.post("/logs", status_code=status.HTTP_202_ACCEPTED, response_model=CountResponse)
async def ingest_logs(
    payload: LogEntriesPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest log entries from Salt minion (NEW).
    
    Log structure per entry:
    {
      "timestamp": "2026-04-17T14:00:00Z",
      "level": "INFO",
      "source": "nginx",
      "message": "Started",
      "metadata": {
        "client_ip": "192.168.1.100",
        "request_id": "12345"
      }
    }
    
    All log entries are stored in database and published to Redis for SSE streaming.
    """
    try:
        # Ingest logs (this is part of the metrics ingestion)
        # The salt_api_client already handles logs in ingest_metrics()
        # This endpoint is for explicit log entries ingestion
        
        # TODO: Implement dedicated log ingestion if needed
        # For now, pass through to metrics ingestion
        metrics_data = {"logs": payload.logs}
        
        await salt_api_client.ingest_metrics(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            metrics_data=metrics_data
        )
        
        logger.info(f"Ingested {len(payload.logs)} log entries from minion {payload.minion_id}")
        return CountResponse(status="accepted", count=len(payload.logs))
        
    except Exception as e:
        logger.error(f"Failed to ingest logs from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest logs: {str(e)}"
        )

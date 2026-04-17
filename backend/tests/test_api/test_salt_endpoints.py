"""
Integration tests for Salt API endpoints.
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.orm import Session

from backend.app.models.server import Server
from backend.app.models.salt_minion import SaltMinion
from backend.app.models.user import User
from backend.app.models.organization import Organization


@pytest.fixture
async def test_server(db_session: Session):
    """Create a test server."""
    server = Server(
        name="Test Server",
        hostname="test-server.example.com",
        ip_address="192.168.1.100",
        port=22,
        is_online=True,
        os_name="Ubuntu",
        os_version="22.04 LTS",
        architecture="amd64",
        cpu_cores=4,
        memory_mb=8192
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


@pytest.fixture
async def test_minion(db_session: Session, test_server):
    """Create a test salt minion."""
    minion = SaltMinion(
        minion_id="test-minion",
        server_id=test_server.id,
        grains_info={
            "os_family": "Debian",
            "osfullname": "Ubuntu",
            "osrelease": "22.04",
            "kernel": "5.15.0-72-generic",
            "hostname": "test-server",
            "fqdn": "test-server.example.com",
            "osarch": "amd64",
            "num_cpus": 4,
            "mem_total": 8589934592
        },
        last_seen=datetime.now(timezone.utc),
        highstate_success=True
    )
    db_session.add(minion)
    db_session.commit()
    db_session.refresh(minion)
    return minion


@pytest.fixture
def auth_headers():
    """Return authentication headers."""
    # In a real test, this would use JWT authentication
    # For now, we'll return mock headers
    return {"Authorization": "Bearer test_token"}


class TestSaltHeartbeatEndpoint:
    """Tests for /api/v1/salt/heartbeat endpoint."""
    
    @pytest.mark.asyncio
    async def test_heartbeat_success(self, client: AsyncClient, test_minion, auth_headers):
        """Test successful heartbeat."""
        response = await client.post(
            "/api/v1/salt/heartbeat",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_heartbeat_missing_minion_id(self, client: AsyncClient, auth_headers):
        """Test heartbeat with missing minion_id."""
        response = await client.post(
            "/api/v1/salt/heartbeat",
            json={
                "server_id": 1,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_heartbeat_invalid_timestamp(self, client: AsyncClient, auth_headers):
        """Test heartbeat with invalid timestamp."""
        response = await client.post(
            "/api/v1/salt/heartbeat",
            json={
                "minion_id": "test-minion",
                "server_id": 1,
                "timestamp": "invalid-timestamp"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestSaltMetricsEndpoint:
    """Tests for /api/v1/salt/metrics endpoint."""
    
    @pytest.mark.asyncio
    async def test_ingest_metrics_success(self, client: AsyncClient, test_minion, auth_headers):
        """Test successful metrics ingestion."""
        metrics = [
            {
                "metric_name": "cpu_total_user",
                "metric_value": 25.5,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "metric_name": "memory_available",
                "metric_value": 4294967296,
                "unit": "bytes",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        response = await client.post(
            "/api/v1/salt/metrics",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "metrics": metrics
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics_processed" in data
        assert data["metrics_processed"] == 2
    
    @pytest.mark.asyncio
    async def test_ingest_metrics_expanded(self, client: AsyncClient, test_minion, auth_headers):
        """Test metrics ingestion with expanded fields."""
        metrics = [
            {
                "metric_name": "cpu_0_user",
                "metric_value": 20.5,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "metric_name": "cpu_0_system",
                "metric_value": 5.0,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "metric_name": "load_1min",
                "metric_value": 0.5,
                "unit": "load_avg",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        response = await client.post(
            "/api/v1/salt/metrics",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "metrics": metrics
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metrics_processed"] == 3
    
    @pytest.mark.asyncio
    async def test_ingest_metrics_empty(self, client: AsyncClient, test_minion, auth_headers):
        """Test metrics ingestion with empty list."""
        response = await client.post(
            "/api/v1/salt/metrics",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "metrics": []
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metrics_processed"] == 0


class TestSaltBeaconEndpoint:
    """Tests for /api/v1/salt/beacon endpoint."""
    
    @pytest.mark.asyncio
    async def test_ingest_beacon_disk_usage(self, client: AsyncClient, test_minion, auth_headers):
        """Test beacon ingestion for disk usage."""
        beacon_data = {
            "beacon_type": "disk_usage",
            "event_data": {
                "mountpoint": "/",
                "used_percent": 85.5,
                "used_gb": 42.75,
                "total_gb": 50.0,
                "fstype": "ext4"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await client.post(
            "/api/v1/salt/beacon",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "beacon_data": beacon_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "event_type" in data
        assert data["event_type"] == "beacon"
    
    @pytest.mark.asyncio
    async def test_ingest_beacon_service_status(self, client: AsyncClient, test_minion, auth_headers):
        """Test beacon ingestion for service status."""
        beacon_data = {
            "beacon_type": "service_status",
            "event_data": {
                "service_name": "nginx",
                "status": "running",
                "pid": 1234
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await client.post(
            "/api/v1/salt/beacon",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "beacon_data": beacon_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_ingest_beacon_invalid_type(self, client: AsyncClient, test_minion, auth_headers):
        """Test beacon ingestion with invalid type."""
        beacon_data = {
            "beacon_type": "invalid_type",
            "event_data": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await client.post(
            "/api/v1/salt/beacon",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "beacon_data": beacon_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Bad request


class TestSaltServicesEndpoint:
    """Tests for /api/v1/salt/services endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_service_state(self, client: AsyncClient, test_minion, auth_headers):
        """Test updating service state."""
        service_data = {
            "services": [
                {
                    "name": "nginx",
                    "status": "running",
                    "pid": 1234
                },
                {
                    "name": "postgresql",
                    "status": "stopped",
                    "pid": None
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await client.post(
            "/api/v1/salt/services",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "service_data": service_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "services_updated" in data
        assert data["services_updated"] == 2
    
    @pytest.mark.asyncio
    async def test_update_service_state_empty(self, client: AsyncClient, test_minion, auth_headers):
        """Test updating service state with empty list."""
        response = await client.post(
            "/api/v1/salt/services",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "service_data": {
                    "services": [],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestSaltProcessesEndpoint:
    """Tests for /api/v1/salt/processes endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_process_list(self, client: AsyncClient, test_minion, auth_headers):
        """Test updating process list."""
        process_data = {
            "processes": [
                {
                    "pid": 1234,
                    "name": "nginx",
                    "command": "nginx: master process",
                    "username": "www-data",
                    "cpu_percent": 2.5,
                    "memory_percent": 1.2,
                    "state": "S",
                    "start_time": datetime.now(timezone.utc).isoformat()
                },
                {
                    "pid": 5678,
                    "name": "postgres",
                    "command": "postgres: main process",
                    "username": "postgres",
                    "cpu_percent": 0.5,
                    "memory_percent": 2.1,
                    "state": "S",
                    "start_time": datetime.now(timezone.utc).isoformat()
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await client.post(
            "/api/v1/salt/processes",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "process_data": process_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "processes_updated" in data
        assert data["processes_updated"] == 2


class TestSaltPackagesEndpoint:
    """Tests for /api/v1/salt/packages endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_packages(self, client: AsyncClient, test_minion, auth_headers):
        """Test updating package list."""
        package_data = {
            "packages": [
                {
                    "name": "nginx",
                    "version": "1.24.0-2",
                    "architecture": "amd64",
                    "source": "dpkg",
                    "is_update_available": True,
                    "installed_date": datetime.now(timezone.utc).isoformat(),
                    "update_version": "1.25.0-1"
                },
                {
                    "name": "postgresql-14",
                    "version": "14.9-1",
                    "architecture": "amd64",
                    "source": "dpkg",
                    "is_update_available": False,
                    "installed_date": datetime.now(timezone.utc).isoformat()
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await client.post(
            "/api/v1/salt/packages",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "package_data": package_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "packages_updated" in data
        assert data["packages_updated"] == 2


class TestSaltLogsEndpoint:
    """Tests for /api/v1/salt/logs endpoint."""
    
    @pytest.mark.asyncio
    async def test_ingest_logs(self, client: AsyncClient, test_minion, auth_headers):
        """Test log ingestion."""
        log_data = {
            "logs": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "log_level": "INFO",
                    "source": "nginx",
                    "message": "Configuration reloaded successfully"
                },
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "log_level": "ERROR",
                    "source": "postgresql",
                    "message": "Connection failed: connection refused"
                }
            ]
        }
        
        response = await client.post(
            "/api/v1/salt/logs",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "log_data": log_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "logs_ingested" in data
        assert data["logs_ingested"] == 2
    
    @pytest.mark.asyncio
    async def test_ingest_logs_with_metadata(self, client: AsyncClient, test_minion, auth_headers):
        """Test log ingestion with metadata."""
        log_data = {
            "logs": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "log_level": "INFO",
                    "source": "nginx",
                    "message": "Configuration reloaded",
                    "metadata": {
                        "config_file": "/etc/nginx/nginx.conf",
                        "pid": 1234
                    }
                }
            ]
        }
        
        response = await client.post(
            "/api/v1/salt/logs",
            json={
                "minion_id": test_minion.minion_id,
                "server_id": test_minion.server_id,
                "log_data": log_data
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["logs_ingested"] == 1


class TestSSEEndpoints:
    """Tests for SSE streaming endpoints."""
    
    @pytest.mark.asyncio
    async def test_metrics_stream(self, client: AsyncClient, auth_headers):
        """Test metrics SSE stream."""
        response = await client.get(
            "/api/v1/stream/metrics?server_id=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        assert "no-cache" in response.headers.get("cache-control", "")
    
    @pytest.mark.asyncio
    async def test_alerts_stream(self, client: AsyncClient, auth_headers):
        """Test alerts SSE stream."""
        response = await client.get(
            "/api/v1/stream/alerts?server_id=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test SSE health check endpoint."""
        response = await client.get("/api/v1/stream/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

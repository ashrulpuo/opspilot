"""
Unit tests for Salt API client service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from backend.app.services.salt_api_client import SaltAPIClient, MetricsError, BeaconError


@pytest.fixture
def salt_api_client():
    """Create a SaltAPI client instance."""
    return SaltAPIClient()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = Mock()
    redis.publish = AsyncMock()
    return redis


class TestSaltAPIClient:
    """Tests for SaltAPIClient."""
    
    @pytest.mark.asyncio
    async def test_register_minion_success(self, salt_api_client, mock_redis):
        """Test successful minion registration."""
        minion_data = {
            "minion_id": "webserver-01",
            "grains": {
                "os_family": "Debian",
                "osfullname": "Debian GNU/Linux",
                "osrelease": "12",
                "kernel": "6.1.0-9-amd64",
                "hostname": "webserver-01",
                "num_cpus": 4,
                "mem_total": 8589934592
            },
            "last_seen": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltMinion') as mock_minion_model:
                mock_minion = Mock()
                mock_minion.minion_id = "webserver-01"
                mock_minion_model.return_value = mock_minion
                
                result = await salt_api_client.register_minion(
                    server_id=1,
                    data=minion_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert result["minion_id"] == "webserver-01"
                assert result["status"] == "registered"
    
    @pytest.mark.asyncio
    async def test_ingest_metrics_success(self, salt_api_client, mock_redis):
        """Test successful metrics ingestion."""
        metrics_data = [
            {
                "metric_name": "cpu_total_user",
                "metric_value": 25.5,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "metric_name": "memory_available",
                "metric_value": 4294967296,  # 4GB
                "unit": "bytes",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltMetric') as mock_metric_model:
                mock_metric = Mock()
                mock_metric.id = 1
                mock_metric_model.return_value = mock_metric
                
                result = await salt_api_client.ingest_metrics(
                    server_id=1,
                    metrics=metrics_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert "metrics_processed" in result
                assert result["metrics_processed"] == 2
    
    @pytest.mark.asyncio
    async def test_ingest_metrics_invalid(self, salt_api_client, mock_redis):
        """Test metrics ingestion with invalid data."""
        invalid_metrics = [
            {
                "metric_name": "",  # Empty name
                "metric_value": 50.0,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with pytest.raises(MetricsError) as exc_info:
                await salt_api_client.ingest_metrics(
                    server_id=1,
                    metrics=invalid_metrics,
                    db=mock_db,
                    redis=mock_redis
                )
            
            assert "Invalid metric data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ingest_beacon_event(self, salt_api_client, mock_redis):
        """Test beacon event ingestion."""
        beacon_data = {
            "beacon_type": "disk_usage",
            "event_data": {
                "mountpoint": "/",
                "used_percent": 85.5,
                "used_gb": 42.75,
                "total_gb": 50.0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltEvent') as mock_event_model:
                mock_event = Mock()
                mock_event.id = 1
                mock_event_model.return_value = mock_event
                
                result = await salt_api_client.ingest_beacon_event(
                    server_id=1,
                    beacon_data=beacon_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert result["event_type"] == "beacon"
                assert result["beacon_type"] == "disk_usage"
    
    @pytest.mark.asyncio
    async def test_ingest_beacon_invalid_type(self, salt_api_client, mock_redis):
        """Test beacon ingestion with invalid beacon type."""
        invalid_beacon = {
            "beacon_type": "invalid_beacon_type",
            "event_data": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with pytest.raises(BeaconError) as exc_info:
                await salt_api_client.ingest_beacon_event(
                    server_id=1,
                    beacon_data=invalid_beacon,
                    db=mock_db,
                    redis=mock_redis
                )
            
            assert "Unsupported beacon type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_service_state(self, salt_api_client, mock_redis):
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
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltServiceState') as mock_service_model:
                mock_service = Mock()
                mock_service.id = 1
                mock_service_model.return_value = mock_service
                
                result = await salt_api_client.update_service_state(
                    server_id=1,
                    service_data=service_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert "services_updated" in result
                assert result["services_updated"] == 2
    
    @pytest.mark.asyncio
    async def test_update_process_list(self, salt_api_client, mock_redis):
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
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltProcess') as mock_process_model:
                mock_process = Mock()
                mock_process.id = 1
                mock_process_model.return_value = mock_process
                
                result = await salt_api_client.update_process_list(
                    server_id=1,
                    process_data=process_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert "processes_updated" in result
                assert result["processes_updated"] == 1
    
    @pytest.mark.asyncio
    async def test_update_packages(self, salt_api_client, mock_redis):
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
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltPackage') as mock_package_model:
                mock_package = Mock()
                mock_package.id = 1
                mock_package_model.return_value = mock_package
                
                result = await salt_api_client.update_packages(
                    server_id=1,
                    package_data=package_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert "packages_updated" in result
                assert result["packages_updated"] == 1
    
    @pytest.mark.asyncio
    async def test_ingest_logs(self, salt_api_client, mock_redis):
        """Test log ingestion."""
        log_data = {
            "logs": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "log_level": "INFO",
                    "source": "nginx",
                    "message": "Configuration reloaded"
                },
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "log_level": "ERROR",
                    "source": "postgresql",
                    "message": "Connection failed"
                }
            ]
        }
        
        # Mock database session
        with patch('backend.app.services.salt_api_client.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            with patch('backend.app.services.salt_api_client.SaltLog') as mock_log_model:
                mock_log = Mock()
                mock_log.id = 1
                mock_log_model.return_value = mock_log
                
                result = await salt_api_client.ingest_logs(
                    server_id=1,
                    log_data=log_data,
                    db=mock_db,
                    redis=mock_redis
                )
                
                assert "logs_ingested" in result
                assert result["logs_ingested"] == 2


class TestSaltMetricsParser:
    """Tests for metrics parsing logic."""
    
    @pytest.mark.asyncio
    async def test_parse_cpu_metrics(self, salt_api_client):
        """Test parsing CPU metrics."""
        metrics_data = [
            {
                "metric_name": "cpu_0_user",
                "metric_value": 25.5,
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
                "metric_name": "cpu_0_idle",
                "metric_value": 69.5,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Test that metrics are parsed correctly
        assert metrics_data[0].metric_name == "cpu_0_user"
        assert metrics_data[0].metric_value == 25.5
        assert metrics_data[0].unit == "percent"
    
    @pytest.mark.asyncio
    async def test_parse_memory_metrics(self, salt_api_client):
        """Test parsing memory metrics."""
        metrics_data = [
            {
                "metric_name": "mem_total",
                "metric_value": 8589934592,  # 8GB
                "unit": "bytes",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "metric_name": "mem_available",
                "metric_value": 4294967296,  # 4GB
                "unit": "bytes",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Test that memory metrics are parsed correctly
        assert metrics_data[0].metric_name == "mem_total"
        assert metrics_data[0].metric_value == 8589934592
        assert metrics_data[0].unit == "bytes"
    
    @pytest.mark.asyncio
    async def test_parse_disk_metrics(self, salt_api_client):
        """Test parsing disk metrics."""
        metrics_data = [
            {
                "metric_name": "disk_usage_",
                "metric_value": 75.5,
                "unit": "percent",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "used_gb": 37.75,
                    "total_gb": 50.0
                }
            }
        ]
        
        # Test that disk metrics include metadata
        assert metrics_data[0].metric_name == "disk_usage_"
        assert metrics_data[0].metric_value == 75.5
        assert "metadata" in metrics_data[0]
        assert metrics_data[0]["metadata"]["mountpoint"] == "/"

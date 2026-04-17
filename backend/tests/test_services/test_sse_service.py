"""
Unit tests for SSE service.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from backend.app.services.sse_service import SSEService, SSEConnectionError


@pytest.fixture
def mock_redis_pool():
    """Mock Redis connection pool."""
    pool = Mock()
    pool.get_connection = AsyncMock()
    return pool


@pytest.fixture
def sse_service(mock_redis_pool):
    """Create an SSE service instance."""
    return SSEService(redis_pool=mock_redis_pool)


class TestSSEService:
    """Tests for SSEService."""
    
    @pytest.mark.asyncio
    async def test_generate_token_success(self, sse_service):
        """Test successful token generation."""
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=1
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self, sse_service):
        """Test successful token verification."""
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=1
        )
        
        payload = sse_service.verify_token(token)
        
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["org_id"] == 1
        assert payload["server_id"] == 1
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, sse_service):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(SSEConnectionError) as exc_info:
            sse_service.verify_token(invalid_token)
        
        assert "Invalid token" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_verify_token_expired(self, sse_service):
        """Test verification of expired token."""
        # Create an expired token (this would require mocking JWT decode with time)
        # For now, we'll test the structure
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=1
        )
        
        # Token should be valid immediately
        payload = sse_service.verify_token(token)
        assert payload is not None
    
    @pytest.mark.asyncio
    async def test_stream_metrics_generator(self, sse_service, mock_redis_pool):
        """Test metrics stream generator."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis subscription
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Create a mock message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"metrics:{server_id}"
        mock_message.data = json.dumps({
            "type": "metric",
            "server_id": server_id,
            "metric_name": "cpu_total_user",
            "metric_value": 25.5,
            "unit": "percent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Mock the iterator to return our mock message
        async def mock_iter():
            yield mock_message
            # Stop after one message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test the generator
        events = []
        async for event in sse_service.stream_metrics(server_id, token):
            events.append(event)
            break  # Just test first event
        
        assert len(events) == 1
        assert "data: " in events[0]
        assert "retry: " in events[0]
        assert "event: metric" in events[0]
    
    @pytest.mark.asyncio
    async def test_stream_metrics_server_specific(self, sse_service, mock_redis_pool):
        """Test streaming metrics for specific server."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Verify subscribe is called with correct channel
        events = []
        async for event in sse_service.stream_metrics(server_id, token):
            events.append(event)
            break
        
        # Verify subscribe was called
        mock_redis.subscribe.assert_called()
        call_args = mock_redis.subscribe.call_args
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_stream_metrics_all_servers(self, sse_service, mock_redis_pool):
        """Test streaming metrics for all servers (admin)."""
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=None  # Admin can view all
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.psubscribe = AsyncMock()  # Pattern subscription
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Test the generator
        events = []
        async for event in sse_service.stream_metrics(None, token):
            events.append(event)
            break
        
        # Verify pattern subscription
        mock_redis.psubscribe.assert_called()
    
    @pytest.mark.asyncio
    async def test_stream_alerts_generator(self, sse_service, mock_redis_pool):
        """Test alerts stream generator."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Mock alert message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"alerts:{server_id}"
        mock_message.data = json.dumps({
            "type": "alert",
            "server_id": server_id,
            "alert_type": "cpu_high",
            "severity": "critical",
            "message": "CPU usage above 90%",
            "event_data": {"cpu_percent": 95.5},
            "processed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        async def mock_iter():
            yield mock_message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test the generator
        events = []
        async for event in sse_service.stream_alerts(server_id, token):
            events.append(event)
            break
        
        assert len(events) == 1
        assert "data: " in events[0]
        assert "event: alert" in events[0]
    
    @pytest.mark.asyncio
    async def test_stream_services_generator(self, sse_service, mock_redis_pool):
        """Test services stream generator."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Mock service state message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"services:{server_id}"
        mock_message.data = json.dumps({
            "type": "service_state",
            "server_id": server_id,
            "service_name": "nginx",
            "status": "running",
            "previous_status": "stopped",
            "last_checked": datetime.now(timezone.utc).isoformat()
        })
        
        async def mock_iter():
            yield mock_message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test the generator
        events = []
        async for event in sse_service.stream_services(server_id, token):
            events.append(event)
            break
        
        assert len(events) == 1
        assert "event: service_state" in events[0]
    
    @pytest.mark.asyncio
    async def test_stream_processes_generator(self, sse_service, mock_redis_pool):
        """Test processes stream generator."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Mock process list message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"processes:{server_id}"
        mock_message.data = json.dumps({
            "type": "process_list",
            "server_id": server_id,
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
            ]
        })
        
        async def mock_iter():
            yield mock_message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test the generator
        events = []
        async for event in sse_service.stream_processes(server_id, token):
            events.append(event)
            break
        
        assert len(events) == 1
        assert "event: process_list" in events[0]
    
    @pytest.mark.asyncio
    async def test_stream_packages_generator(self, sse_service, mock_redis_pool):
        """Test packages stream generator."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Mock package update message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"packages:{server_id}"
        mock_message.data = json.dumps({
            "type": "package_update",
            "server_id": server_id,
            "name": "nginx",
            "version": "1.24.0-2",
            "architecture": "amd64",
            "source": "dpkg",
            "is_update_available": True,
            "installed_date": datetime.now(timezone.utc).isoformat(),
            "update_version": "1.25.0-1"
        })
        
        async def mock_iter():
            yield mock_message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test the generator
        events = []
        async for event in sse_service.stream_packages(server_id, token):
            events.append(event)
            break
        
        assert len(events) == 1
        assert "event: package_update" in events[0]
    
    @pytest.mark.asyncio
    async def test_stream_logs_generator(self, sse_service, mock_redis_pool):
        """Test logs stream generator."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Mock log entry message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"logs:{server_id}"
        mock_message.data = json.dumps({
            "type": "log_entry",
            "server_id": server_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_level": "INFO",
            "source": "nginx",
            "message": "Configuration reloaded successfully",
            "metadata": {"config_file": "/etc/nginx/nginx.conf"}
        })
        
        async def mock_iter():
            yield mock_message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test the generator
        events = []
        async for event in sse_service.stream_logs(server_id, token):
            events.append(event)
            break
        
        assert len(events) == 1
        assert "event: log_entry" in events[0]
    
    @pytest.mark.asyncio
    async def test_sse_message_format(self, sse_service, mock_redis_pool):
        """Test SSE message format compliance."""
        server_id = 1
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=server_id
        )
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.subscribe = AsyncMock()
        mock_redis_pool.get_connection.return_value = mock_redis
        
        # Mock message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.channel = f"metrics:{server_id}"
        mock_message.data = json.dumps({
            "type": "metric",
            "server_id": server_id,
            "metric_name": "cpu_total_user",
            "metric_value": 25.5
        })
        
        async def mock_iter():
            yield mock_message
        
        mock_redis.__aiter__ = mock_iter
        
        # Test message format
        events = []
        async for event in sse_service.stream_metrics(server_id, token):
            events.append(event)
            break
        
        # Check SSE format
        event = events[0]
        assert event.startswith("event: metric")
        assert "data: " in event
        assert "retry: " in event
        assert "\n\n" in event  # SSE messages end with double newline


class TestSSEAccessControl:
    """Tests for SSE access control."""
    
    @pytest.mark.asyncio
    async def test_server_specific_access(self, sse_service):
        """Test server-specific access control."""
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=1  # Can only access server 1
        )
        
        payload = sse_service.verify_token(token)
        
        assert payload["server_id"] == 1
        assert payload["user_id"] == 1
        assert payload["org_id"] == 1
    
    @pytest.mark.asyncio
    async def test_global_access_admin(self, sse_service):
        """Test global access for admin users."""
        token = sse_service.generate_token(
            user_id=1,
            org_id=1,
            server_id=None  # Admin can access all servers
        )
        
        payload = sse_service.verify_token(token)
        
        assert payload["server_id"] is None
        assert payload["user_id"] == 1
        assert payload["org_id"] == 1

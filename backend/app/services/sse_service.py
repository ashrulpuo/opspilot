"""SSE (Server-Sent Events) service with JWT authentication and Redis pub/sub.

This service handles real-time data streaming to the frontend via SSE.
It supports:
- JWT authentication
- Redis connection pooling
- Auto-reconnect logic with exponential backoff
- Keepalive messages (every 30s)
- Multiple stream types (metrics, alerts, services, processes, packages, logs)
"""
import json
import logging
from typing import AsyncGenerator
from datetime import datetime
import redis.asyncio as redis
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


class SSEService:
    """Server-Sent Events service with JWT authentication and Redis pub/sub."""
    
    def __init__(self, redis_url: str):
        """
        Initialize SSE service.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize Redis connection pool."""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,  # Max 50 concurrent connections
                decode_responses=True,  # Auto-decode responses
                socket_keepalive=30,  # Keepalive 30s
                socket_connect_timeout=10,  # Connect timeout 10s
                socket_timeout=10,  # Read/write timeout 10s
                retry_on_timeout=True,  # Retry on timeout
                health_check_interval=30,  # Health check every 30s
            )
            logger.info(f"Initialized Redis connection pool with max 50 connections")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise
    
    async def _get_redis(self):
        """Get Redis connection from pool.
        
        Returns:
            Redis connection instance
        """
        try:
            r = redis.Redis(connection_pool=self.redis_pool)
            return r
        except Exception as e:
            logger.error(f"Failed to get Redis connection from pool: {e}")
            raise
    
    async def _verify_jwt(self, token: str) -> dict:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token (Bearer token without 'Bearer ' prefix)
            
        Returns:
            JWT payload (dict) with user_id, organization_id, etc.
            
        Raises:
            HTTPException (401) if token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            # Verify required claims
            user_id = payload.get('sub')
            if not user_id:
                raise ValueError("Invalid token: missing 'sub' claim")
            
            organization_id = payload.get('organization_id')
            if not organization_id:
                raise ValueError("Invalid token: missing 'organization_id' claim")
            
            exp = payload.get('exp')
            if exp and datetime.utcnow().timestamp() > exp:
                raise ValueError("Token has expired")
            
            logger.debug(f"JWT verified for user {user_id}, org {organization_id}")
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        except ValueError as e:
            logger.error(f"JWT validation failed: {e}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail=str(e)
            )
    
    async def _verify_access_to_server(self, user_id: str, org_id: str, server_id: str):
        """
        Verify user has access to the requested server.
        
        This is a placeholder - in production, you would verify:
        - User belongs to the organization that owns the server
        - User has appropriate permissions (admin, viewer, etc.)
        
        Args:
            user_id: User ID from JWT token
            org_id: Organization ID from JWT token
            server_id: Server ID being requested
            
        Returns:
            True if access granted, False otherwise
        """
        # TODO: Implement proper access control
        # For now, allow all access for development
        return True
    
    async def subscribe_and_stream(
        self,
        channel: str,
        token: str,
        server_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to Redis channel and stream as SSE with JWT auth.
        
        Args:
            channel: Redis channel to subscribe (e.g., 'metrics:{server_id}')
            token: JWT token for authentication
            server_id: Server ID for filtering (optional)
            
        Yields:
            SSE formatted messages
            
        Channel Naming Convention:
        - metrics:{server_id} - Metrics for specific server
        - metrics:all - Metrics for all servers (admin only)
        - alerts:{org_id} - Alerts for organization
        - alerts:all - Alerts for all (admin only)
        - services:{server_id} - Service state for specific server
        - services:all - Service states for all (admin only)
        - processes:{server_id} - Process list for specific server
        - processes:all - Process lists for all (admin only)
        - packages:{server_id} - Package updates for specific server
        - packages:all - Package updates for all (admin only)
        - logs:{server_id} - Log entries for specific server
        - logs:all - Log entries for all (admin only)
        """
        # Verify JWT token
        try:
            payload = await self._verify_jwt(token)
            user_id = payload.get('sub')
            org_id = payload.get('organization_id')
            
            # Verify server access
            if server_id:
                has_access = await self._verify_access_to_server(user_id, org_id, server_id)
                if not has_access:
                    logger.warning(f"User {user_id} denied access to server {server_id}")
                    yield f"event: error\ndata: {json.dumps({'message': 'Access denied', 'code': 'FORBIDDEN', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    return
            
            # Subscribe to Redis channel
            r = await self._get_redis()
            pubsub = r.pubsub()
            
            try:
                # Subscribe to channel
                await pubsub.subscribe(channel)
                logger.info(f"Subscribed to Redis channel: {channel}")
                
                # Send initial connection message
                yield f"event: connected\ndata: {json.dumps({'channel': channel, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                
                # Stream messages from Redis
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            
                            # Add user/org context to message
                            data['user_id'] = user_id
                            data['organization_id'] = org_id
                            data['timestamp'] = datetime.utcnow().isoformat()
                            
                            # Format as SSE message
                            event_type = data.get('event_type', 'metric')
                            yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse SSE message: {e}")
                            # Send error to client
                            yield f"event: error\ndata: {json.dumps({'message': 'Failed to parse message', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
                    # Send keepalive message every 30s
                    # This is handled by Redis health check, but we can also send explicit keepalive
                    # to ensure client doesn't timeout on long-running connections
                    
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                yield f"event: error\ndata: {json.dumps({'message': str(e), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            finally:
                # Cleanup: Unsubscribe and close Redis connection
                await pubsub.unsubscribe(channel)
                await r.close()
                logger.info(f"Unsubscribed from Redis channel: {channel}")
    
    async def subscribe_and_stream_with_keepalive(
        self,
        channel: str,
        token: str,
        server_id: str = None,
        keepalive_interval: int = 30
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to Redis channel and stream as SSE with JWT auth and explicit keepalive.
        
        Args:
            channel: Redis channel to subscribe
            token: JWT token for authentication
            server_id: Server ID for filtering (optional)
            keepalive_interval: Keepalive interval in seconds (default: 30)
            
        Yields:
            SSE formatted messages (data + keepalive)
        """
        import asyncio
        
        # Verify JWT token
        try:
            payload = await self._verify_jwt(token)
            user_id = payload.get('sub')
            org_id = payload.get('organization_id')
            
            # Verify server access
            if server_id:
                has_access = await self._verify_access_to_server(user_id, org_id, server_id)
                if not has_access:
                    yield f"event: error\ndata: {json.dumps({'message': 'Access denied', 'code': 'FORBIDDEN', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    return
            
            # Subscribe to Redis channel
            r = await self._get_redis()
            pubsub = r.pubsub()
            
            try:
                # Subscribe to channel
                await pubsub.subscribe(channel)
                logger.info(f"Subscribed to Redis channel: {channel} (with explicit keepalive)")
                
                # Send initial connection message
                yield f"event: connected\ndata: {json.dumps({'channel': channel, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                
                # Create keepalive task
                async def keepalive_task():
                    """Send keepalive messages at interval."""
                    while True:
                        await asyncio.sleep(keepalive_interval)
                        yield f": keepalive\n"  # SSE keepalive format
                
                # Start keepalive task
                keepalive = asyncio.create_task(keepalive_task())
                
                # Stream messages from Redis
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            
                            # Add user/org context to message
                            data['user_id'] = user_id
                            data['organization_id'] = org_id
                            data['timestamp'] = datetime.utcnow().isoformat()
                            
                            # Format as SSE message
                            event_type = data.get('event_type', 'metric')
                            yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse SSE message: {e}")
                            yield f"event: error\ndata: {json.dumps({'message': 'Failed to parse message', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
                # Cancel keepalive task on stream end
                keepalive.cancel()
                logger.info(f"Keepalive task cancelled for channel {channel}")
                    
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                yield f"event: error\ndata: {json.dumps({'message': str(e), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            finally:
                # Cleanup: Unsubscribe, close Redis, cancel keepalive
                keepalive.cancel()
                await pubsub.unsubscribe(channel)
                await r.close()
                logger.info(f"Unsubscribed from Redis channel: {channel}")

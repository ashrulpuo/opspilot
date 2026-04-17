# SaltStack Data Collection Implementation Plan

**ID:** 002
**Category:** infrastructure
**Date:** 2026-04-17
**Status:** 📋 Ready to Implement

## Clarifications (Before Implementation)

| Question | Answer | Impact |
|----------|--------|--------|
| **Salt Master Setup?** | No master - minions push directly to backend API | Simplified architecture, no reactor needed |
| **Minion Deployment?** | Already installed on all servers | Skip auto-installation phase |
| **Expected Scale?** | ~50 servers now, scaling to 500+ | Design for scalability |
| **SSE Authentication?** | Yes, use JWT | Secure streaming |
| **Data Retention?** | Need to suggest best practices | See recommendation below |

---

## Data Retention Recommendation

Based on TimescaleDB best practices for monitoring data:

| Metric Type | Retention | Rationale |
|-------------|-----------|------------|
| **CPU, Memory, Load** | 90 days | Standard monitoring retention |
| **Disk Usage** | 365 days | Capacity planning needs longer history |
| **Network I/O** | 30 days | High volume, lower value |
| **Process Data** | 7 days | High churn, recent only |
| **Service State** | 365 days | Audit trail for changes |
| **Alerts/Events** | 365 days | Compliance and incident history |
| **Grains (Static)** | Permanent | Update on refresh only |

**TimescaleDB Compression:**
- 90% compression ratio
- 360GB raw → 36GB compressed
- Automatic with hypertables

**Automatic Cleanup:**
```sql
-- Add to TimescaleDB for automatic data retention
SELECT add_retention_policy('metrics', INTERVAL '90 days');
SELECT add_retention_policy('disk_metrics', INTERVAL '365 days');
SELECT add_retention_policy('service_states', INTERVAL '365 days');
```

---

## Revised Architecture (No Master)

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Dashboard    │  │ Alerts Panel │  │ Server List  │   │
│  │ (Real-time) │  │ (Events)    │  │ (Status)    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼──────────────────────────┼─────────────────┼─────────────┘
          │ JWT Auth          │ JWT Auth          │ JWT Auth
          │                   │                   │
┌─────────┼──────────────────────────┼─────────────────┼─────────────┐
│  ┌─────▼───────────────────────────────────────┐   │
│  │       Backend (FastAPI)                   │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │ Auth (JWT)                          │  │   │
│  │  │ SSE Endpoints (Async Generators)      │  │   │
│  │  │ - stream_metrics() → Redis pub/sub    │  │   │
│  │  │ - stream_alerts() → Redis pub/sub    │  │   │
│  │  │ - stream_status() → Redis pub/sub    │  │   │
│  │  └─────────────────┬────────────────────┘  │   │
│  │                    │                     │   │
│  │  ┌─────────────────▼────────────────────┐  │   │
│  │  │  TimescaleDB (Metrics Store)       │  │   │
│  │  └───────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
          │                 │
          ┌───────────┼─────────────┐
          │           │             │
     ┌────▼────┐  ┌──▼────────┐   ┌──▼────────┐
     │ Server 1 │  │ Server 2  │   │ Server N   │
     │ (Minion) │  │ (Minion)  │   │ (Minion)   │
     │ Salt API │  │ Salt API  │   │ Salt API    │
     │  Push     │  │  Push     │   │ Push       │
     └───────────┘  └───────────┘   └──────────────┘
```

**Key Changes from PRD:**
- ❌ No Salt Master (simpler)
- ✅ Minions push directly to backend API
- ❌ No Salt Reactor (not needed)
- ✅ Backend publishes to Redis for SSE
- ✅ JWT authentication on SSE endpoints

---

## Implementation Plan

### Phase 4: Backend Implementation

#### 4.1 Update Database Schema

**File:** `backend/alembic/versions/xxx_add_salt_tables.py`

```python
"""Add SaltStack tables.

Revision ID: xxx
Revises: xxx
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # Salt minions table
    op.create_table(
        'salt_minions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('minion_id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('last_highstate', sa.DateTime(), nullable=True),
        sa.Column('os_info', postgresql.JSONB(), nullable=False),
        sa.Column('grains_info', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_salt_minions_minion_id', 'salt_minions', ['minion_id'])
    op.create_index('idx_salt_minions_server_id', 'salt_minions', ['server_id'])
    op.create_index('idx_salt_minions_last_seen', 'salt_minions', ['last_seen'])
    
    # Salt events table (for beacon alerts)
    op.create_table(
        'salt_events',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_tag', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_salt_events_server_id', 'salt_events', ['server_id'])
    op.create_index('idx_salt_events_type', 'salt_events', ['event_type'])
    op.create_index('idx_salt_events_processed', 'salt_events', ['processed'])
    op.create_index('idx_salt_events_created_at', 'salt_events', ['created_at'])
    
    # Service states table
    op.create_table(
        'salt_service_states',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('service_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),  # 'running', 'stopped', 'unknown'
        sa.Column('previous_status', sa.String(), nullable=True),
        sa.Column('last_checked', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_service_states_server_id', 'salt_service_states', ['server_id'])
    op.create_index('idx_service_states_service_name', 'salt_service_states', ['server_name', 'server_id'])
    
    # Update Metric model to support more metric types
    op.add_column('metrics', 'unit', sa.String(), nullable=True))
    op.add_column('metrics', 'metadata', postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_table('salt_service_states')
    op.drop_table('salt_events')
    op.drop_table('salt_minions')
    op.drop_column('metrics', 'metadata')
    op.drop_column('metrics', 'unit')
```

---

#### 4.2 Create Salt Models

**File:** `backend/app/models/salt_minion.py`

```python
"""Salt minion model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltMinion(Base):
    """Salt minion model."""
    
    __tablename__ = "salt_minions"
    
    id = Column(String, primary_key=True)
    minion_id = Column(String, nullable=False, index=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    last_seen = Column(DateTime, nullable=False, index=True)
    last_highstate = Column(DateTime, nullable=True)
    os_info = Column(postgresql.JSONB, nullable=False)
    grains_info = Column(postgresql.JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="salt_minion")
    events = relationship("SaltEvent", back_populates="minion", cascade="all, delete-orphan")
    service_states = relationship("SaltServiceState", back_populates="minion", cascade="all, delete-orphan")


class SaltEvent(Base):
    """Salt event (beacon alerts)."""
    
    __tablename__ = "salt_events"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    event_tag = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # 'cpu_alert', 'memory_alert', etc.
    event_data = Column(postgresql.JSONB, nullable=False)
    processed = Column(String, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    server = relationship("Server", back_populates="events")
    minion = relationship("SaltMinion", back_populates="events")


class SaltServiceState(Base):
    """Salt service state."""
    
    __tablename__ = "salt_service_states"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'running', 'stopped', 'unknown'
    previous_status = Column(String, nullable=True)
    last_checked = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="service_states")
    minion = relationship("SaltMinion", back_populates="service_states")
```

**Update:** `backend/app/models/server.py` - Add relationship

```python
class Server(Base):
    # ... existing fields ...
    
    # Add relationships
    salt_minion = relationship("SaltMinion", back_populates="server", uselist=False)
    salt_events = relationship("SaltEvent", back_populates="server", cascade="all, delete-orphan")
    service_states = relationship("SaltServiceState", back_populates="server", cascade="all, delete-orphan")
```

---

#### 4.3 Create Salt API Integration Service

**File:** `backend/app/services/salt_api_client.py`

```python
"""Salt API client service for receiving minion data."""
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.models.server import Server
from app.models.salt_minion import SaltMinion, SaltEvent, SaltServiceState
from app.models.metrics import Metric

logger = logging.getLogger(__name__)


class SaltAPIClient:
    """Salt API client for receiving data from minions."""
    
    def __init__(self):
        """Initialize Salt API client."""
        self.api_key = settings.salt_api_key
        self.timeout = settings.salt_api_timeout
        self.max_retries = settings.salt_api_max_retries
    
    async def register_minion(
        self,
        minion_id: str,
        server_id: str,
        grains: Dict[str, Any],
        os_info: Dict[str, Any]
    ) -> SaltMinion:
        """
        Register or update minion registration.
        
        Args:
            minion_id: Salt minion ID
            server_id: OpsPilot server ID
            grains: All grains data
            os_info: OS information subset
        """
        from app.core.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        
        async with get_db() as db:
            # Check if minion already exists
            result = await db.execute(
                select(SaltMinion).where(SaltMinion.minion_id == minion_id)
            )
            minion = result.scalar_one_or_none()
            
            now = datetime.utcnow()
            
            if minion:
                # Update existing minion
                minion.last_seen = now
                minion.os_info = os_info
                minion.grains_info = grains
                minion.updated_at = now
            else:
                # Create new minion
                minion = SaltMinion(
                    id=f"minion_{minion_id}",
                    minion_id=minion_id,
                    server_id=server_id,
                    last_seen=now,
                    os_info=os_info,
                    grains_info=grains
                )
                db.add(minion)
            
            await db.commit()
            await db.refresh(minion)
            
            logger.info(f"Minion {minion_id} registered/updated for server {server_id}")
            return minion
    
    async def ingest_metrics(
        self,
        minion_id: str,
        server_id: str,
        metrics_data: Dict[str, Any]
    ) -> List[Metric]:
        """
        Ingest metrics from Salt minion.
        
        Args:
            minion_id: Salt minion ID
            server_id: OpsPilot server ID
            metrics_data: Raw metrics from minion
        """
        from app.core.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        
        metrics = []
        now = datetime.utcnow()
        
        async with get_db() as db:
            # Parse and store each metric
            # CPU metrics
            if 'cpu_stats' in metrics_data:
                cpu_data = metrics_data['cpu_stats']
                for core_name, core_data in cpu_data.items():
                    if core_name.startswith('cpu'):
                        for metric_type, value in core_data.items():
                            if metric_type in ['user', 'system', 'idle']:
                                metric = Metric(
                                    id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_{metric_type}",
                                    server_id=server_id,
                                    timestamp=now,
                                    metric_name=f"cpu_{core_name}_{metric_type}",
                                    metric_value=float(value),
                                    unit='%'
                                )
                                db.add(metric)
                                metrics.append(metric)
            
            # Memory metrics
            if 'mem_info' in metrics_data:
                mem_data = metrics_data['mem_info']
                total_mb = mem_data.get('MemTotal', 0)
                available_mb = mem_data.get('MemAvailable', 0)
                used_percent = ((total_mb - available_mb) / total_mb * 100) if total_mb > 0 else 0
                
                metric = Metric(
                    id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_memory_percent",
                    server_id=server_id,
                    timestamp=now,
                    metric_name='memory_percent',
                    metric_value=used_percent,
                    unit='%'
                )
                db.add(metric)
                metrics.append(metric)
            
            # Disk metrics
            if 'disk_usage' in metrics_data:
                disk_data = metrics_data['disk_usage']
                for mount, disk_info in disk_data.items():
                    if isinstance(disk_info, dict):
                        percent = disk_info.get('percent', 0)
                        used_gb = disk_info.get('used', 0) / (1024**3)
                        total_gb = disk_info.get('total', 0) / (1024**3)
                        
                        metric = Metric(
                            id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_disk_{mount.replace('/', '_')}",
                            server_id=server_id,
                            timestamp=now,
                            metric_name=f'disk_usage_{mount.replace('/', '_')}',
                            metric_value=percent,
                            unit='%'
                        )
                        db.add(metric)
                        metrics.append(metric)
            
            # Network metrics
            if 'net_dev' in metrics_data:
                net_data = metrics_data['net_dev']
                for interface, if_data in net_data.items():
                    if isinstance(if_data, dict):
                        rx_bps = if_data.get('rx_bytes', 0)  # Convert to bps later via aggregation
                        tx_bps = if_data.get('tx_bytes', 0)
                        
                        metric = Metric(
                            id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_network_rx_{interface}",
                            server_id=server_id,
                            timestamp=now,
                            metric_name=f'network_rx_{interface}',
                            metric_value=float(rx_bps),
                            unit='bps',
                            metadata={'interface': interface}
                        )
                        db.add(metric)
                        metrics.append(metric)
            
            await db.commit()
            
            # Update minion last_seen
            result = await db.execute(
                select(SaltMinion).where(SaltMinion.minion_id == minion_id)
            )
            minion = result.scalar_one_or_none()
            if minion:
                minion.last_seen = now
                await db.commit()
            
            logger.info(f"Ingested {len(metrics)} metrics from minion {minion_id}")
            return metrics
    
    async def ingest_beacon_event(
        self,
        minion_id: str,
        server_id: str,
        event_tag: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> SaltEvent:
        """
        Ingest beacon event (alert).
        
        Args:
            minion_id: Salt minion ID
            server_id: OpsPilot server ID
            event_tag: Event tag (e.g., 'salt/beacon/load/')
            event_type: Event type (e.g., 'cpu_alert', 'memory_alert')
            event_data: Event data
        """
        from app.core.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        
        async with get_db() as db:
            event = SaltEvent(
                id=f"event_{server_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                server_id=server_id,
                event_tag=event_tag,
                event_type=event_type,
                event_data=event_data,
                created_at=datetime.utcnow()
            )
            
            db.add(event)
            await db.commit()
            
            logger.info(f"Beacon event {event_type} from minion {minion_id}")
            return event
    
    async def update_service_state(
        self,
        minion_id: str,
        server_id: str,
        service_name: str,
        status: str
    ) -> SaltServiceState:
        """
        Update or create service state.
        
        Args:
            minion_id: Salt minion ID
            server_id: OpsPilot server ID
            service_name: Service name
            status: Service status ('running', 'stopped', 'unknown')
        """
        from app.core.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        
        async with get_db() as db:
            # Check if service state exists
            result = await db.execute(
                select(SaltServiceState).where(
                    SaltServiceState.server_id == server_id,
                    SaltServiceState.service_name == service_name
                )
            )
            service_state = result.scalar_one_or_none()
            
            now = datetime.utcnow()
            
            if service_state:
                # Update existing
                previous_status = service_state.status
                service_state.status = status
                service_state.previous_status = previous_status
                service_state.last_checked = now
            else:
                # Create new
                service_state = SaltServiceState(
                    id=f"service_{server_id}_{service_name}",
                    server_id=server_id,
                    service_name= service_name,
                    status=status,
                    last_checked=now
                )
                db.add(service_state)
            
            await db.commit()
            
            # Publish to Redis for SSE
            await self._publish_service_state(server_id, service_name, status)
            
            logger.info(f"Service {service_name} on server {server_id}: {status}")
            return service_state
    
    async def _publish_service_state(self, server_id: str, service_name: str, status: str):
        """Publish service state change to Redis."""
        import redis.asyncio as redis
        
        r = redis.Redis.from_url(settings.redis_url)
        
        message = {
            'server_id': server_id,
            'service_name': service_name,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await r.publish(f"service_state:{server_id}", message)
        await r.close()
```

---

#### 4.4 Update Server Model

**File:** `backend/app/models/server.py`

```python
# Add these relationships to the Server class

class Server(Base):
    # ... existing fields ...
    
    # New relationships
    salt_minion = relationship("SaltMinion", back_populates="server", uselist=False)
    salt_events = relationship("SaltEvent", back_populates="server", cascade="all, delete-orphan")
    service_states = relationship("SaltServiceState", back_populates="server", cascade="all, delete-orphan")
```

---

#### 4.5 Create SSE Service with JWT Auth

**File:** `backend/app/services/sse_service.py`

```python
"""SSE service with JWT authentication."""
import json
import logging
from typing import AsyncGenerator
import redis.asyncio as redis

from fastapi import Depends, HTTPException
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import get_current_user

logger = logging.getLogger(__name__)


class SSEService:
    """Server-Sent Events service with authentication."""
    
    def __init__(self, redis_url: str):
        """Initialize SSE service."""
        self.redis_url = redis_url
        self.redis_pool = None
    
    async def _get_redis(self):
        """Get Redis connection from pool."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,
                decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)
    
    async def _verify_jwt(self, token: str) -> dict:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
    
    async def subscribe_and_stream(
        self,
        channel: str,
        token: str
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to Redis channel and stream as SSE with JWT auth.
        
        Args:
            channel: Redis channel to subscribe
            token: JWT token for authentication
            
        Yields:
            SSE formatted messages
        """
        # Verify JWT
        payload = await self._verify_jwt(token)
        user_id = payload.get('sub')
        organization_id = payload.get('organization_id')
        
        # Verify user has access to this channel
        # (For server-specific channels, verify server belongs to user's org)
        # (For org-wide channels, verify user_id is in org)
        
        r = await self._get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    # Add user/org context to message
                    data['user_id'] = user_id
                    data['organization_id'] = organization_id
                    
                    # Format as SSE message
                    event_type = data.get('event_type', 'metric')
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        finally:
            await pubsub.unsubscribe(channel)
            await r.close()
```

---

#### 4.6 Create SSE Endpoints

**File:** `backend/app/api/v1/stream.py`

```python
"""SSE endpoints for real-time updates."""
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
import logging

from app.services.sse_service import SSEService
from app.core.security import verify_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stream", tags=["SSE"])

# Initialize SSE service
sse_service = SSEService(redis_url=settings.redis_url)


@router.get("/metrics")
async def stream_metrics(
    server_id: str = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream real-time metrics via SSE with JWT auth.
    
    Query params:
        server_id: Stream specific server (optional, default: all)
    
    Headers:
        Authorization: JWT Bearer token
    """
    # Verify JWT token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    # Build channel name
    if server_id:
        channel = f"metrics:{server_id}"
    else:
        channel = "metrics:all"
    
    return StreamingResponse(
        sse_service.subscribe_and_stream(channel, token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/alerts")
async def stream_alerts(
    server_id: str = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream alerts via SSE with JWT auth.
    
    Query params:
        server_id: Stream specific server (optional, default: all)
    
    Headers:
        Authorization: JWT Bearer token
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    # Build channel name
    if server_id:
        channel = f"alerts:{server_id}"
    else:
        channel = "alerts:all"
    
    return StreamingResponse(
        sse_service.subscribe_and_stream(channel, token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/services")
async def stream_services(
    server_id: str = Query(None, description="Server ID to filter"),
    authorization: str = Header(..., alias="Authorization")
):
    """
    Stream service state changes via SSE with JWT auth.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    channel = f"services:{server_id}" if server_id else "services:all"
    
    return StreamingResponse(
        sse_service.subscribe_and_stream(channel, token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

---

#### 4.7 Create Salt API Ingestion Endpoint

**File:** `backend/app/api/v1/salt_ingest.py` (new file)

```python
"""Salt API ingestion endpoint for receiving data from minions."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.services.salt_api_client import SaltAPIClient
from app.core.database import get_db
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
    metrics: Dict[str, Any] = Field(..., description="Raw metrics from Salt status modules")
    # Expected structure:
    # {
    #   "cpu_stats": { ... },
    #   "mem_info": { ... },
    #   "disk_usage": { ... },
    #   "net_dev": { ... },
    #   "load_avg": { ... }
    # }


class BeaconEventPayload(BaseModel):
    """Beacon event payload from minion."""
    minion_id: str
    server_id: str
    timestamp: str
    beacon_type: str  # 'cpu_alert', 'memory_alert', 'disk_alert', 'service_alert'
    beacon_data: Dict[str, Any]


class ServiceStatePayload(BaseModel):
    """Service state payload from minion."""
    minion_id: str
    server_id: str
    timestamp: str
    services: Dict[str, str]  # { "nginx": "running", "mysql": "stopped", ... }


# ============================================
# Endpoints
# ============================================

@router.post("/heartbeat", status_code=status.HTTP_202_ACCEPTED)
async def minion_heartbeat(
    payload: MinionHeartbeat,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Receive heartbeat from Salt minion.
    
    This updates the minion's last_seen timestamp.
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
        await salt_api_client.register_minion(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            grains=payload.grains or {},
            os_info=os_info
        )
        
        logger.info(f"Heartbeat from minion {payload.minion_id} (server {payload.server_id})")
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"Failed to process heartbeat from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process heartbeat: {str(e)}"
        )


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(
    payload: MetricsPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest metrics from Salt minion.
    
    Expected metrics structure from Salt status modules:
    - cpu_stats: status.cpustats
    - mem_info: status.meminfo
    - disk_usage: status.diskusage
    - net_dev: status.netdev
    - load_avg: status.loadavg
    """
    try:
        metrics = await salt_api_client.ingest_metrics(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            metrics_data=payload.metrics
        )
        
        logger.info(f"Ingested {len(metrics)} metrics from minion {payload.minion_id}")
        return {
            "status": "accepted",
            "metrics_count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest metrics from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest metrics: {str(e)}"
        )


@router.post("/beacon", status_code=status.HTTP_202_ACCEPTED)
async def ingest_beacon_event(
    payload: BeaconEventPayload,
    api_key: str = Depends(verify_salt_api_key)
):
    """
    Ingest beacon event (alert) from Salt minion.
    
    Beacon types:
    - cpu_alert: CPU usage exceeded threshold
    - memory_alert: Memory usage exceeded threshold
    - disk_alert: Disk usage exceeded threshold
    - service_alert: Service state changed
    """
    try:
        event = await salt_api_client.ingest_beacon_event(
            minion_id=payload.minion_id,
            server_id=payload.server_id,
            event_tag=f"salt/beacon/{payload.beacon_type}/",
            event_type=payload.beacon_type,
            event_data=payload.beacon_data
        )
        
        # Publish to Redis for SSE
        await salt_api_client._publish_event_to_redis(
            server_id=payload.server_id,
            event_type=payload.beacon_type,
            event_data=payload.beacon_data
        )
        
        logger.info(f"Beacon event {payload.beacon_type} from minion {payload.minion_id}")
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"Failed to ingest beacon event from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest beacon event: {str(e)}"
        )


@router.post("/services", status_code=status.HTTP_202_ACCEPTED)
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
      "docker": "running"
    }
    """
    try:
        for service_name, service_status in payload.services.items():
            await salt_api_client.update_service_state(
                minion_id=payload.minion_id,
                server_id=payload.server_id,
                service_name=service_name,
                status=service_status
            )
        
        logger.info(f"Ingested {len(payload.services)} service states from minion {payload.minion_id}")
        return {
            "status": "accepted",
            "services_count": len(payload.services)
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest service states from {payload.minion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest service states: {str(e)}"
        )
```

---

### Phase 5: Frontend Implementation

#### 5.1 Create SSE Composable

**File:** `frontend/src/composables/useSaltStream.ts`

```typescript
import { ref, onUnmounted } from 'vue'
import type { Ref } from 'vue'

interface Metric {
  id: string
  server_id: string
  timestamp: string
  metric_name: string
  metric_value: number
  unit: string
  metadata?: Record<string, any>
}

interface Alert {
  id: string
  server_id: string
  event_type: string
  event_tag: string
  event_data: Record<string, any>
  processed: boolean
  created_at: string
}

interface ServiceState {
  id: string
  server_id: string
  service_name: string
  status: string
  previous_status?: string
  last_checked: string
}

export function useSaltStream(serverId: string) {
  const metrics = ref<Record<string, Metric>>({})
  const alerts = ref<Alert[]>([])
  const serviceStates = ref<Record<string, string>>({})
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const MAX_RECONNECT_ATTEMPTS = 5
  
  const connectMetrics = () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.error('No auth token available')
      return
    }
    
    const es = new EventSource(`/api/v1/stream/metrics?server_id=${serverId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    es.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'metric') {
          metrics.value[data.metric_name] = data
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }
    
    es.onerror = (error: Event) => {
      console.error('SSE connection error:', error)
      isConnected.value = false
      
      // Exponential backoff reconnection
      if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
        setTimeout(connectMetrics, delay)
        reconnectAttempts.value++
      } else {
        console.error('Max reconnection attempts reached')
      }
    }
    
    es.onopen = () => {
      console.log('SSE metrics connection opened')
      isConnected.value = true
      reconnectAttempts.value = 0
    }
    
    window.metricsEventSource = es
  }
  
  const connectAlerts = () => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    
    const es = new EventSource(`/api/v1/stream/alerts?server_id=${serverId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    es.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.event_type === 'alert') {
          alerts.value.unshift(data)
          // Keep only last 50 alerts
          if (alerts.value.length > 50) {
            alerts.value = alerts.value.slice(0, 50)
          }
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }
    
    es.onerror = (error: Event) => {
      console.error('SSE alerts connection error:', error)
      // Reconnect logic
      if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
        setTimeout(connectAlerts, 5000)
        reconnectAttempts.value++
      }
    }
    
    es.onopen = () => {
      console.log('SSE alerts connection opened')
      isConnected.value = true
      reconnectAttempts.value = 0
    }
    
    window.alertsEventSource = es
  }
  
  const connectServices = () => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    
    const es = new EventSource(`/api/v1/stream/services?server_id=${serverId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    es.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'service_state') {
          serviceStates.value[data.service_name] = data.status
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }
    
    es.onerror = (error: Event) => {
      console.error('SSE services connection error:', error)
      // Reconnect logic
      if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
        setTimeout(connectServices, 5000)
        reconnectAttempts.value++
      }
    }
    
    es.onopen = () => {
      console.log('SSE services connection opened')
      isConnected.value = true
      reconnectAttempts.value = 0
    }
    
    window.servicesEventSource = es
  }
  
  const disconnectAll = () => {
    if (window.metricsEventSource) {
      window.metricsEventSource.close()
    }
    if (window.alertsEventSource) {
      window.alertsEventSource.close()
    }
    if (window.servicesEventSource) {
      window.servicesEventSource.close()
    }
    isConnected.value = false
  }
  
  // Auto-connect on mount
  connectMetrics()
  connectAlerts()
  connectServices()
  
  // Cleanup on unmount
  onUnmounted(() => {
    disconnectAll()
  })
  
  return {
    metrics,
    alerts,
    serviceStates,
    isConnected,
    reconnectAttempts,
    disconnectAll
  }
}
```

---

#### 5.2 Update Server Detail Page

**File:** `frontend/src/views/servers/detail/index.vue`

```vue
<template>
  <div class="server-detail">
    <ServerDetailHeader :server-id="serverId" />
    
    <el-tabs v-model="activeTab">
      <!-- Overview Tab -->
      <el-tab-pane label="Overview" name="overview">
        <ServerOverview :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Metrics Tab (Real-time) -->
      <el-tab-pane label="Metrics" name="metrics">
        <ServerMetrics :server-id="serverId" :real-time="true" />
      </el-tab-pane>
      
      <!-- Salt Info Tab -->
      <el-tab-pane label="Salt Info" name="salt">
        <SaltMinionInfo :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Services Tab (Real-time) -->
      <el-tab-pane label="Services" name="services">
        <SaltServices :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Alerts Tab -->
      <el-tab-pane label="Alerts" name="alerts">
        <SaltAlerts :server-id="serverId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSaltStream } from '@/composables/useSaltStream'

const route = useRoute()
const serverId = route.params.id as string
const activeTab = ref('overview')

// Use Salt SSE composable
const {
  metrics,
  alerts,
  serviceStates,
  isConnected,
  disconnectAll
} = useSaltStream(serverId)

onMounted(() => {
  console.log('Server detail page mounted for server:', serverId)
  console.log('SSE connected:', isConnected.value)
})
</script>

<style scoped>
.server-detail {
  padding: 20px;
}
</style>
```

---

## Implementation Steps

### Step 1: Database Migration (30 min)
- [ ] Create migration file `xxx_add_salt_tables.py`
- [ ] Run migration `alembic upgrade head`
- [ ] Verify tables created

### Step 2: Backend Models (1 hour)
- [ ] Create `SaltMinion` model
- [ ] Create `SaltEvent` model
- [ ] Create `SaltServiceState` model
- [ ] Update `Server` model with relationships
- [ ] Update `Metric` model (unit, metadata fields)

### Step 3: Salt API Service (2 hours)
- [ ] Create `SaltAPIClient` service
- [ ] Implement `register_minion()` method
- [ ] Implement `ingest_metrics()` method
- [ ] Implement `ingest_beacon_event()` method
- [ ] Implement `update_service_state()` method
- [ ] Add Redis publishing helpers
- [ ] Add error handling and logging

### Step 4: SSE Service (1.5 hours)
- [ ] Create `SSEService` class
- [ ] Implement JWT verification
- [ ] Implement `subscribe_and_stream()` method
- [ ] Add Redis connection pooling
- [ ] Add keepalive messages
- [ ] Add proper error handling

### Step 5: SSE Endpoints (1.5 hours)
- [ ] Create `/api/v1/stream/metrics` endpoint
- [ ] Create `/api/v1/stream/alerts` endpoint
- [ ] Create `/api/v1/stream/services` endpoint
- [ ] Add JWT authentication to all endpoints
- [ ] Add server_id filtering
- [ ] Add proper headers (no-cache, keep-alive)
- [ ] Test SSE endpoints manually

### Step 6: Salt Ingestion API (2 hours)
- [ ] Create `/api/v1/salt/heartbeat` endpoint
- [ ] Create `/api/v1/salt/metrics` endpoint
- [ ] Create `/api/v1/salt/beacon` endpoint
- [ ] Create `/api/v1/salt/services` endpoint
- [ ] Add Salt API key verification
- [ ] Test ingestion endpoints manually

### Step 7: Frontend SSE Composable (1.5 hours)
- [ ] Create `useSaltStream.ts` composable
- [ ] Implement metrics subscription
- [ ] Implement alerts subscription
- [ ] Implement services subscription
- [ ] Add JWT auth headers
- [ ] Add reconnection logic
- [ ] Add cleanup on unmount

### Step 8: Update Server Detail Page (1 hour)
- [ ] Add tabs for Overview, Metrics, Salt Info, Services, Alerts
- [ ] Integrate `useSaltStream` composable
- [ ] Display real-time metrics
- [ ] Display real-time alerts
- [ ] Display real-time service states

### Step 9: Create Salt Info Component (1 hour)
- [ ] Create `SaltMinionInfo.vue` component
- [ ] Display grains data
- [ ] Display minion status
- [ ] Display OS info
- [ ] Add refresh button

### Step 10: Create Salt Metrics Component (1.5 hours)
- [ ] Create `SaltMetrics.vue` component
- [ ] Display CPU charts (real-time)
- [ ] Display memory charts (real-time)
- [ ] Display disk usage (real-time)
- [ ] Display network I/O (real-time)
- [ ] Add time range selector

### Step 11: Create Salt Services Component (1 hour)
- [ ] Create `SaltServices.vue` component
- [ ] Display service list
- [ ] Show service status (running/stopped/unknown)
- [ ] Add restart service button
- [ ] Display last checked time

### Step 12: Create Salt Alerts Component (1 hour)
- [ ] Create `SaltAlerts.vue` component
- [ ] Display alert list
- [ ] Show alert severity (info/warning/critical)
- [ ] Add alert filtering
- [ ] Add alert acknowledge button

### Step 13: Update Main App Router (15 min)
- [ ] Register SSE endpoints in main router
- [ ] Register salt ingestion endpoints in main router
- [ ] Add route for server detail with Salt tabs

### Step 14: Testing (2 hours)
- [ ] Test SSE connections manually
- [ ] Test JWT authentication
- [ ] Test metrics ingestion
- [ ] Test beacon events
- [ ] Test service state updates
- [ ] Test reconnection logic
- [ ] Test concurrent connections (simulate 50 clients)

### Step 15: Documentation (1 hour)
- [ ] Update API documentation
- [ ] Document SSE endpoints
- [ ] Document authentication flow
- [ ] Create frontend integration guide
- [ ] Update deployment docs

---

## Total Estimated Time

| Phase | Estimated Time |
|-------|--------------|
| **Phase 4: Backend** | ~8.5 hours |
| **Phase 5: Frontend** | ~8 hours |
| **Testing & Documentation** | ~3 hours |
| **Total** | ~19.5 hours (2.5 days) |

---

## Questions Before Starting

Before I begin Phase 4 (Implementation), please confirm:

1. ✅ **Architecture confirmed:** No Salt master, minions push directly to backend
2. ✅ **Minions installed:** Already on servers, no auto-install needed
3. ✅ **Scale:** ~50 servers → 500+
4. ✅ **SSE Auth:** JWT authentication required
5. ✅ **Data retention:** 90-365 days as recommended
6. ⚠️ **Backend tech stack:** FastAPI + SQLAlchemy async + TimescaleDB (confirmed)
7. ⚠️ **Frontend tech stack:** Vue 3 + TypeScript + Pinia + Element Plus (confirmed)
8. ⚠️ **SSE implementation:** As approved in plan

**Ready to proceed with Phase 4 (Implementation)?**

---

**Related Enhancements:**
- `001-saltstack-sse.md` - SSE design reference

**Related Issues:**
- None yet

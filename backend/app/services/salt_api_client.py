"""Salt API client service for receiving data from minions.

This service handles:
- Minion registration (grains)
- Metrics ingestion (CPU, Memory, Disk, Network, Processes, Packages, Logs)
- Beacon events (alerts)
- Service state updates
- Package information
- Log ingestion

All data is stored in database and published to Redis for SSE streaming.
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.models.server import Server
from app.models.salt_minion import SaltMinion
from app.models.salt_event import SaltEvent
from app.models.salt_service_state import SaltServiceState
from app.models.salt_process import SaltProcess
from app.models.salt_package import SaltPackage
from app.models.salt_log import SaltLog
from app.models.metrics import Metric

from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SaltAPIClient:
    """Salt API client for receiving data from minions."""
    
    def __init__(self):
        """Initialize Salt API client."""
        self.api_key = settings.salt_api_key
        self.timeout = settings.salt_api_timeout
        self.max_retries = settings.salt_api_max_retries
        
        # Redis connection for publishing SSE events
        self.redis_url = settings.redis_url
        self.redis_pool = None
    
    async def _get_redis(self):
        """Get Redis connection from pool."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,
                decode_responses=True,
                decode_retry=True
            )
        return redis.Redis(connection_pool=self.redis_pool)
    
    async def _publish_event(self, channel: str, event_data: Dict[str, Any]):
        """Publish event to Redis for SSE streaming."""
        try:
            r = await self._get_redis()
            await r.publish(channel, event_data)
            logger.debug(f"Published event to channel {channel}: {event_data}")
        except Exception as e:
            logger.error(f"Failed to publish event to Redis: {e}")
    
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
            Expected structure:
            {
              "cpu_stats": { ... },  # status.cpustats
              "mem_info": { ... },   # status.meminfo
              "disk_usage": { ... }, # status.diskusage
              "disk_stats": { ... }, # status.diskstats
              "net_dev": { ... },   # status.netdev
              "net_stats": { ... },  # status.netstats
              "load_avg": { ... },   # status.loadavg
              "processes": { ... },  # status.procs
              "packages": { ... },  # pkg.list_pkgs
            }
        """
        from app.models.salt_process import SaltProcess
        from app.models.salt_package import SaltPackage
        
        metrics = []
        now = datetime.utcnow()
        
        async with get_db() as db:
            # Parse and store each metric type
            
            # CPU metrics
            if 'cpu_stats' in metrics_data:
                cpu_data = metrics_data['cpu_stats']
                for core_name, core_data in cpu_data.items():
                    if isinstance(core_data, dict) and core_name.startswith('cpu'):
                        for metric_type, value in core_data.items():
                            if metric_type in ['user', 'system', 'idle']:
                                metric = Metric(
                                    id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_cpu_{core_name}_{metric_type}",
                                    server_id=server_id,
                                    timestamp=now,
                                    metric_name=f"cpu_{core_name}_{metric_type}",
                                    metric_value=float(value),
                                    unit='%',
                                    metadata={'core': core_name}
                                )
                                db.add(metric)
                                metrics.append(metric)
            
            # Memory metrics
            if 'mem_info' in metrics_data:
                mem_data = metrics_data['mem_info']
                total_mb = float(mem_data.get('MemTotal', 0))
                available_mb = float(mem_data.get('MemAvailable', 0))
                used_percent = ((total_mb - available_mb) / total_mb * 100) if total_mb > 0 else 0
                
                metric = Metric(
                    id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_memory_percent",
                    server_id=server_id,
                    timestamp=now,
                    metric_name='memory_percent',
                    metric_value=used_percent,
                    unit='%',
                    metadata={'total_mb': total_mb, 'available_mb': available_mb}
                )
                db.add(metric)
                metrics.append(metric)
            
            # Load metrics
            if 'load_avg' in metrics_data:
                load_data = metrics_data['load_avg']
                
                for period in ['1min', '5min', '15min']:
                    value = float(load_data.get(period, 0))
                    metric = Metric(
                        id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_load_{period}",
                        server_id=server_id,
                        timestamp=now,
                        metric_name=f'load_{period}',
                        metric_value=value,
                        unit='load',
                        metadata={'period': period}
                    )
                    db.add(metric)
                    metrics.append(metric)
            
            # Disk metrics
            if 'disk_usage' in metrics_data:
                disk_usage = metrics_data['disk_usage']
                
                for mount, disk_info in disk_usage.items():
                    if isinstance(disk_info, dict):
                        percent = float(disk_info.get('percent', 0))
                        used_gb = float(disk_info.get('used', 0)) / (1024**3)
                        total_gb = float(disk_info.get('total', 0)) / (1024**3)
                        
                        metric = Metric(
                            id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_disk_usage_{mount.replace('/', '_')}",
                            server_id=server_id,
                            timestamp=now,
                            metric_name=f'disk_usage_{mount.replace('/', '_')}',
                            metric_value=percent,
                            unit='%',
                            metadata={
                                'mount': mount,
                                'used_gb': used_gb,
                                'total_gb': total_gb
                            }
                        )
                        db.add(metric)
                        metrics.append(metric)
            
            # Disk I/O metrics
            if 'disk_stats' in metrics_data:
                disk_stats = metrics_data['disk_stats']
                
                for disk, stats in disk_stats.items():
                    if isinstance(stats, dict):
                        reads_mb = float(stats.get('reads_sectors', 0)) * 512 / (1024**2)
                        writes_mb = float(stats.get('writes_sectors', 0)) * 512 / (1024**2)
                        reads_ms = float(stats.get('reads_ms', 0))
                        writes_ms = float(stats.get('writes_ms', 0))
                        
                        # Throughput (bytes/sec)
                        if reads_ms > 0:
                            read_bps = reads_mb / (reads_ms / 1000)  # MB/sec
                        else:
                            read_bps = 0
                        if writes_ms > 0:
                            write_bps = writes_mb / (writes_ms / 1000)  # MB/sec
                        else:
                            write_bps = 0
                        
                        # I/O wait (percentage)
                        io_wait = 0.0
                        total_time = reads_ms + writes_ms
                        if total_time > 0:
                            io_wait = ((stats.get('io_ms', 0) * 1000) / total_time) / 100
                            
                        metric = Metric(
                            id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_disk_io_{disk}",
                            server_id=server_id,
                            timestamp=now,
                            metric_name=f'disk_io_{disk}_read_bps',
                            metric_value=read_bps,
                            unit='bps',
                            metadata={
                                'disk': disk,
                                'reads_mb': reads_mb,
                                'writes_mb': writes_mb,
                                'read_bps': read_bps,
                                'write_bps': write_bps,
                                'io_wait': io_wait
                            }
                        )
                        db.add(metric)
                        metrics.append(metric)
            
            # Network metrics
            if 'net_dev' in metrics_data:
                net_dev = metrics_data['net_dev']
                
                for interface, if_data in net_dev.items():
                    if isinstance(if_data, dict):
                        rx_bytes = float(if_data.get('rx_bytes', 0))
                        tx_bytes = float(if_data.get('tx_bytes', 0))
                        rx_packets = float(if_data.get('rx_packets', 0))
                        tx_packets = float(if_data.get('tx_packets', 0))
                        
                        metric = Metric(
                            id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_network_rx_{interface}",
                            server_id=server_id,
                            timestamp=now,
                            metric_name=f'network_rx_{interface}',
                            metric_value=rx_bytes,
                            unit='bytes',
                            metadata={'interface': interface}
                        )
                        db.add(metric)
                        metrics.append(metric)
                        
                        metric = Metric(
                            id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_network_tx_{interface}",
                            server_id=server_id,
                            timestamp=now,
                            metric_name=f'network_tx_{interface}',
                            metric_value=tx_bytes,
                            unit='bytes',
                            metadata={'interface': interface}
                        )
                        db.add(metric)
                        metrics.append(metric)
            
            # Network stats (TCP/UDP connections)
            if 'net_stats' in metrics_data:
                net_stats = metrics_data['net_stats']
                
                # TCP metrics
                if 'Tcp' in net_stats:
                    tcp_data = net_stats['Tcp']
                    
                    active_opens = int(tcp_data.get('CurrEstab', 0))
                    active = int(tcp_data.get('ActiveOpens', 0))
                    passive_opens = int(tcp_data.get('PassiveOpens', 0))
                    
                    metric = Metric(
                        id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_tcp_connections",
                        server_id=server_id,
                        timestamp=now,
                        metric_name='tcp_connections',
                        metric_value=active_opens,
                        unit='count',
                        metadata={
                            'active_opens': active_opens,
                            'passive_opens': passive_opens
                        }
                    )
                    db.add(metric)
                    metrics.append(metric)
                
                # UDP metrics
                if 'Udp' in net_stats:
                    udp_data = net_stats['Udp']
                    in_datagrams = int(udp_data.get('InDatagrams', 0))
                    out_datagrams = int(udp_data.get('OutDatagrams', 0))
                    
                    metric = Metric(
                        id=f"{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}_udp_datagrams",
                        server_id=server_id,
                        timestamp=now,
                        metric_name='udp_datagrams',
                        metric_value=in_datagrams,
                        unit='count',
                        metadata={
                            'in_datagrams': in_datagrams,
                            'out_datagrams': out_datagrams
                        }
                    )
                    db.add(metric)
                    metrics.append(metric)
            
            # Process metrics
            if 'processes' in metrics_data:
                processes = metrics_data.get('processes', [])
                
                for proc_data in processes:
                    if isinstance(proc_data, dict):
                        process = SaltProcess(
                            id=f"proc_{server_id}_{proc_data.get('pid', 0)}",
                            server_id=server_id,
                            pid=int(proc_data.get('pid', 0)),
                            name=proc_data.get('name', ''),
                            command=proc_data.get('cmd', proc_data.get('command', '')),
                            username=proc_data.get('user', ''),
                            cpu_percent=float(proc_data.get('cpu_percent', 0)),
                            memory_percent=float(proc_data.get('mem_percent', 0)),
                            state=proc_data.get('state', ''),
                            start_time=datetime.utcnow(),  # Placeholder if not provided
                        )
                        db.add(process)
            
            # Package metrics
            if 'packages' in metrics_data:
                packages = metrics_data.get('packages', {})
                
                for pkg_name, pkg_info in packages.items():
                    if isinstance(pkg_info, dict):
                        package = SaltPackage(
                            id=f"pkg_{server_id}_{pkg_name}",
                            server_id=server_id,
                            name=pkg_name,
                            version=pkg_info.get('version', ''),
                            architecture=pkg_info.get('arch', ''),
                            source=pkg_info.get('source', ''),
                            is_update_available=False,  # Default, update with check
                            installed_date=datetime.utcnow()
                        )
                        db.add(package)
            
            # Log metrics
            if 'logs' in metrics_data:
                logs = metrics_data.get('logs', [])
                
                for log_data in logs:
                    if isinstance(log_data, dict) or isinstance(log_data, list):
                        # Handle both dict and list formats
                        log_entries = [log_data] if isinstance(log_data, dict) else log_data]
                        
                        for log_entry in log_entries:
                            log = SaltLog(
                                id=f"log_{server_id}_{now.strftime('%Y%m%d%H%M%S%f')}",
                                server_id=server_id,
                                timestamp=datetime.utcnow(),
                                log_level=log_entry.get('level', 'INFO') if isinstance(log_entry, dict) else 'INFO',
                                source=log_entry.get('source', '') if isinstance(log_entry, dict) else '',
                                message=str(log_entry) if isinstance(log_entry, dict) else str(log_entry)
                            )
                            db.add(log)
            
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
            event_type: Event type (e.g., 'cpu_alert', 'memory_alert', 'disk_alert', 'service_alert')
            event_data: Event data (thresholds, values, etc.)
        """
        async with get_db() as db:
            event = SaltEvent(
                id=f"event_{server_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                server_id=server_id,
                event_tag=event_tag,
                event_type=event_type,
                event_data=event_data,
                processed=False,
                created_at=datetime.utcnow()
            )
            
            db.add(event)
            await db.commit()
            await db.refresh(event)
            
            # Publish to Redis for SSE
            await self._publish_event(
                channel=f"salt_events:{server_id}",
                event_data={
                    'server_id': server_id,
                    'event_tag': event_tag,
                    'event_type': event_type,
                    'event_data': event_data,
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Beacon event {event_type} from minion {minion_id}")
            return event
    
    async def ingest_packages(
        self,
        minion_id: str,
        server_id: str,
        packages_list: List[Dict[str, Any]]
    ) -> List[SaltPackage]:
        """
        Ingest package list from Salt minion.
        
        Args:
            minion_id: Salt minion ID
            server_id: OpsPilot server ID
            packages_list: List of packages with metadata
        """
        packages = []
        
        async with get_db() as db:
            for pkg_info in packages_list:
                if isinstance(pkg_info, dict):
                    pkg_name = pkg_info.get('name', '')
                    version = pkg_info.get('version', '')
                    architecture = pkg_info.get('arch', '')
                    source = pkg_info.get('source', '')
                    
                    # Check for available update
                    is_update_available = False
                    if 'is_update_available' in pkg_info:
                        is_update_available = bool(pkg_info['is_update_available'])
                    
                    package = SaltPackage(
                        id=f"pkg_{server_id}_{pkg_name}",
                        server_id=server_id,
                        name=pkg_name,
                        version=version,
                        architecture=architecture,
                        source=source,
                        is_update_available=is_update_available,
                        installed_date=datetime.utcnow(),
                        update_version=pkg_info.get('update_version', '') if is_update_available else None
                    )
                    
                    db.add(package)
                    packages.append(package)
            
            await db.commit()
            
            logger.info(f"Ingested {len(packages)} packages from minion {minion_id}")
            return packages
    
    async def ingest_logs(
        self,
        minion_id: str,
        server_id: str,
        logs_list: List[Dict[str, Any]]
    ) -> List[SaltLog]:
        """
        Ingest log entries from Salt minion.
        
        Args:
            minion_id: Salt minion ID
            server_id: OpsPilot server ID
            logs_list: List of log entries
        """
        logs = []
        
        async with get_db() as db:
            for log_data in logs_list:
                if isinstance(log_data, dict) or isinstance(log_data, list):
                    # Handle both dict and list formats
                    log_entries = [log_data] if isinstance(log_data, dict) else log_data]
                    
                    for log_entry in log_entries:
                        log = SaltLog(
                            id=f"log_{server_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                            server_id=server_id,
                            timestamp=datetime.utcnow(),
                            log_level=log_entry.get('level', 'INFO') if isinstance(log_entry, dict) else 'INFO',
                            source=log_entry.get('source', '') if isinstance(log_entry, dict) else '',
                            message=str(log_entry) if isinstance(log_entry, dict) else str(log_entry)
                        )
                        db.add(log)
            
            await db.commit()
            
            logger.info(f"Ingested {len(logs)} log entries from minion {minion_id}")
            return logs
    
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
                # Update existing service state
                previous_status = service_state.status
                service_state.status = status
                service_state.previous_status = previous_status
                service_state.last_checked = now
            else:
                # Create new service state
                service_state = SaltServiceState(
                    id=f"service_{server_id}_{service_name}",
                    server_id=server_id,
                    service_name=service_name,
                    status=status,
                    previous_status=None,
                    last_checked=now
                )
                db.add(service_state)
            
            await db.commit()
            await db.refresh(service_state)
            
            # Publish to Redis for SSE
            await self._publish_event(
                channel=f"services:{server_id}",
                event_data={
                    'server_id': server_id,
                    'service_name': service_name,
                    'status': status,
                    'previous_status': service_state.previous_status if service_state else None,
                    'last_checked': now.isoformat()
                }
            )
            
            logger.info(f"Service {service_name} on server {server_id}: {status}")
            return service_state

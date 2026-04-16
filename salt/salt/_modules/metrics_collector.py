#!/usr/bin/env python3
"""
OpsPilot Salt Runner - Metrics Collector
Collects system metrics and sends to OpsPilot backend API
"""

import json
import time
import psutil
import requests
import socket


def get_system_metrics():
    """Collect comprehensive system metrics."""
    hostname = socket.gethostname()
    
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_load_avg = [x / cpu_count for x in psutil.getloadavg()]
    
    # Memory metrics
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used = memory.used / (1024**3)  # GB
    memory_total = memory.total / (1024**3)  # GB
    
    # Disk metrics
    disk_usage = {}
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_usage[partition.mountpoint] = {
                'percent': usage.percent,
                'used_gb': usage.used / (1024**3),
                'total_gb': usage.total / (1024**3),
                'free_gb': usage.free / (1024**3),
                'mountpoint': partition.mountpoint
            }
        except PermissionError:
            continue
    
    # Network metrics
    network_io = psutil.net_io_counters()
    
    # Uptime
    boot_time = psutil.boot_time()
    uptime = time.time() - boot_time
    
    # Load average
    load_avg = psutil.getloadavg()
    
    # Process count
    process_count = len(psutil.pids())
    
    return {
        'hostname': hostname,
        'timestamp': time.time(),
        'cpu': {
            'percent': cpu_percent,
            'count': cpu_count,
            'load_avg': cpu_load_avg,
        },
        'memory': {
            'percent': memory_percent,
            'used_gb': round(memory_used, 2),
            'total_gb': round(memory_total, 2),
        },
        'disk': disk_usage,
        'network': {
            'bytes_sent': network_io.bytes_sent,
            'bytes_recv': network_io.bytes_recv,
            'packets_sent': network_io.packets_sent,
            'packets_recv': network_io.packets_recv,
        },
        'uptime': {
            'seconds': int(uptime),
            'hours': round(uptime / 3600, 2),
        },
        'load_average': {
            '1min': load_avg[0],
            '5min': load_avg[1],
            '15min': load_avg[2],
        },
        'processes': {
            'count': process_count,
        },
    }


def send_metrics_to_backend(metrics, api_url, api_key, server_id, organization_id):
    """Send metrics to OpsPilot backend API."""
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
    }
    
    payload = {
        'server_id': server_id,
        'organization_id': organization_id,
        'metrics': metrics,
    }
    
    try:
        response = requests.post(
            f'{api_url}/servers/{server_id}/metrics',
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return {'status': 'success', 'response': response.json()}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': str(e)}


def main():
    """Main execution function."""
    try:
        # Get API configuration from pillar
        __opts__ = salt.config.client_config()
        
        # Read configuration
        pillar = __opts__['pillar'].get('opspilot', {})
        api_url = pillar.get('api_url', 'http://localhost:9000/api/v1')
        api_key = pillar.get('api_key', '')
        organization_id = pillar.get('organization_id', '')
        server_id = __grains__['id']
        
        if not api_key:
            print("ERROR: OpsPilot API key not configured")
            return
        
        # Collect metrics
        metrics = get_system_metrics()
        
        # Send to backend
        result = send_metrics_to_backend(
            metrics, api_url, api_key, server_id, organization_id
        )
        
        print(f"Metrics sent: {result['status']}")
        if result['status'] == 'error':
            print(f"ERROR: {result.get('message', 'Unknown error')}")
        else:
            print(f"Backend response: {result.get('response', {})}")
        
    except Exception as e:
        print(f"ERROR: Failed to collect metrics: {str(e)}")


if __name__ == '__main__':
    main()

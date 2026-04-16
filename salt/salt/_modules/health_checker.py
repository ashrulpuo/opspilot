#!/usr/bin/env python3
"""
OpsPilot Salt Runner - Health Checker
Performs system health checks and reports to OpsPilot backend
"""

import json
import requests
import socket
import time
from datetime import datetime


def check_service(host, port, name, timeout=5):
    """Check if a service is running on a port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return {
            'service': name,
            'status': 'up',
            'host': host,
            'port': port,
            'response_time_ms': result * 1000,  # Convert to milliseconds
        }
    except socket.timeout:
        return {
            'service': name,
            'status': 'timeout',
            'host': host,
            'port': port,
            'response_time_ms': timeout * 1000,
        }
    except socket.error as e:
        return {
            'service': name,
            'status': 'down',
            'host': host,
            'port': port,
            'error': str(e),
            'response_time_ms': None,
        }


def check_disk_usage(threshold=85):
    """Check disk usage and alert if above threshold."""
    import psutil
    disk_usage = {}
    
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_usage[partition.mountpoint] = {
                'percent': usage.percent,
                'used_gb': round(usage.used / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'mountpoint': partition.mountpoint,
                'status': 'warning' if usage.percent >= threshold else 'ok',
            }
        except PermissionError:
            continue
    
    return disk_usage


def check_memory_usage(threshold=90):
    """Check memory usage and alert if above threshold."""
    import psutil
    memory = psutil.virtual_memory()
    
    return {
        'percent': memory.percent,
        'used_gb': round(memory.used / (1024**3), 2),
        'total_gb': round(memory.total / (1024**3), 2),
        'available_gb': round(memory.available / (1024**3), 2),
        'status': 'warning' if memory.percent >= threshold else 'ok',
    }


def check_cpu_usage(threshold=90):
    """Check CPU usage and alert if above threshold."""
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    load_avg = psutil.getloadavg()
    
    return {
        'percent': cpu_percent,
        'count': cpu_count,
        'load_avg': {
            '1min': load_avg[0],
            '5min': load_avg[1],
            '15min': load_avg[2],
        },
        'status': 'warning' if cpu_percent >= threshold else 'ok',
    }


def check_uptime():
    """Check system uptime."""
    import psutil
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_days = uptime_seconds / 86400
    uptime_hours = (uptime_seconds % 86400) / 3600
    
    return {
        'uptime_seconds': int(uptime_seconds),
        'uptime_days': int(uptime_days),
        'uptime_hours': int(uptime_hours),
        'status': 'ok',
    }


def perform_health_checks(config):
    """Perform all configured health checks."""
    checks = {}
    
    # Service checks
    checks['services'] = []
    for service in config.get('services', []):
        result = check_service(
            service['host'],
            service['port'],
            service['name']
        )
        checks['services'].append(result)
    
    # System resource checks
    checks['disk'] = check_disk_usage(config.get('disk_threshold', 85))
    checks['memory'] = check_memory_usage(config.get('memory_threshold', 90))
    checks['cpu'] = check_cpu_usage(config.get('cpu_threshold', 90))
    checks['uptime'] = check_uptime()
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'server_id': config.get('server_id', ''),
        'organization_id': config.get('organization_id', ''),
        'checks': checks,
        'overall_status': 'healthy' if all([
            all(s.get('status') == 'ok' for s in checks.get('services', [])),
            checks['disk']['status'] == 'ok',
            checks['memory']['status'] == 'ok',
            checks['cpu']['status'] == 'ok',
        ]) else 'warning',
    }


def send_health_report(api_url, api_key, health_report):
    """Send health report to OpsPilot backend."""
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
    }
    
    try:
        import requests
        response = requests.post(
            f'{api_url}/servers/{health_report["server_id"]}/health',
            json=health_report,
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
        import salt.config
        pillar = salt.config.client_config()
        api_url = pillar.get('api_url', 'http://localhost:9000/api/v1')
        api_key = pillar.get('api_key', '')
        server_id = pillar.get('server_id', '')
        organization_id = pillar.get('organization_id', '')
        
        if not api_key:
            print("ERROR: OpsPilot API key not configured")
            return
        
        # Get health check configuration
        config = pillar.get('health_checks', {})
        config['server_id'] = server_id
        config['organization_id'] = organization_id
        
        # Perform health checks
        health_report = perform_health_checks(config)
        
        # Send to backend
        result = send_health_report(api_url, api_key, health_report)
        
        print(f"Health check completed: {health_report['overall_status']}")
        print(f"Services checked: {len(health_report['checks'].get('services', []))}")
        print(f"Disk status: {health_report['checks'].get('disk', {}).get('status', 'unknown')}")
        print(f"Memory status: {health_report['checks'].get('memory', {}).get('status', 'unknown')}")
        print(f"CPU status: {health_report['checks'].get('cpu', {}).get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            print(f"Backend response: {result.get('response', {})}")
        else:
            print(f"ERROR: Failed to send health report: {result.get('message', 'Unknown error')}")
        
    except Exception as e:
        print(f"ERROR: Health check failed: {str(e)}")


if __name__ == '__main__':
    main()

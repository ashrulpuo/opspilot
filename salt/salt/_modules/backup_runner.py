#!/usr/bin/env python3
"""
OpsPilot Salt Runner - Backup Runner
Executes rsync backup jobs with validation and reporting
"""

import json
import subprocess
import sys
import os
import time
from datetime import datetime


def run_rsync_backup(backup_config, server_id):
    """Execute rsync backup with validation."""
    sources = backup_config.get('sources', [])
    destinations = backup_config.get('destinations', [])
    exclude_patterns = backup_config.get('exclude', [])
    
    if not sources or not destinations:
        return {
            'status': 'error',
            'message': 'No backup sources or destinations configured'
        }
    
    # Build rsync command
    exclude_args = ['--exclude=' + pat for pat in exclude_patterns]
    rsync_cmd = ['rsync', '-avz', '--progress'] + exclude_args
    
    results = []
    
    for dest in destinations:
        for source in sources:
            # Add source and destination
            cmd = rsync_cmd + [source, dest]
            
            # Add compression if enabled
            if backup_config.get('compress', False):
                cmd.insert(2, '-z')  # Insert after -avz
            
            try:
                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                end_time = time.time()
                duration = end_time - start_time
                
                # Parse output for statistics
                stats = parse_rsync_output(result.stdout)
                
                results.append({
                    'source': source,
                    'destination': dest,
                    'duration_seconds': round(duration, 2),
                    'files_transferred': stats.get('files', 0),
                    'bytes_transferred': stats.get('bytes', 0),
                    'success': result.returncode == 0,
                    'error': result.stderr if result.stderr else None,
                    'timestamp': datetime.utcnow().isoformat(),
                })
                
            except subprocess.TimeoutExpired:
                results.append({
                    'source': source,
                    'destination': dest,
                    'duration_seconds': 0,
                    'files_transferred': 0,
                    'bytes_transferred': 0,
                    'success': False,
                    'error': 'Timeout exceeded',
                    'timestamp': datetime.utcnow().isoformat(),
                })
                
            except Exception as e:
                results.append({
                    'source': source,
                    'destination': dest,
                    'duration_seconds': 0,
                    'files_transferred': 0,
                    'bytes_transferred': 0,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                })
    
    return {
        'status': 'complete',
        'results': results,
        'total_files': sum(r.get('files_transferred', 0) for r in results),
        'total_bytes': sum(r.get('bytes_transferred', 0) for r in results),
    }


def parse_rsync_output(output):
    """Parse rsync verbose output for statistics."""
    stats = {'files': 0, 'bytes': 0}
    
    # Look for "sent X bytes, received Y bytes" pattern
    import re
    match = re.search(r'sent ([\d,]+) bytes', output)
    if match:
        stats['bytes'] = int(match.group(1))
    
    # Count file transfers
    file_count = len(re.findall(r'(\.[-/\\\w]+)$', output))
    stats['files'] = file_count
    
    return stats


def send_backup_report(api_url, api_key, server_id, organization_id, backup_results):
    """Send backup report to OpsPilot backend."""
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
    }
    
    payload = {
        'server_id': server_id,
        'organization_id': organization_id,
        'backup_results': backup_results,
    }
    
    try:
        import requests
        response = requests.post(
            f'{api_url}/servers/{server_id}/backups',
            json=payload,
            headers=headers,
            timeout=60,
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
        pillar = __opts__['pillar'].get('opspilot', {})
        api_url = pillar.get('api_url', 'http://localhost:9000/api/v1')
        api_key = pillar.get('api_key', '')
        organization_id = pillar.get('organization_id', '')
        server_id = __grains__['id']
        backup_pillar = pillar.get('backup', {})
        
        if not api_key:
            print("ERROR: OpsPilot API key not configured")
            sys.exit(1)
        
        # Get backup configuration from pillar
        backup_configs = backup_pillar.get('jobs', [])
        
        if not backup_configs:
            print("ERROR: No backup jobs configured in pillar")
            sys.exit(1)
        
        # Execute each backup job
        all_results = []
        for job_config in backup_configs:
            result = run_rsync_backup(job_config, server_id)
            all_results.extend(result.get('results', []))
        
        # Send report to backend
        report = {
            'server_id': server_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_jobs': len(backup_configs),
            'successful_jobs': sum(1 for r in all_results if r.get('success', False)),
            'total_files': sum(r.get('files_transferred', 0) for r in all_results),
            'total_bytes': sum(r.get('bytes_transferred', 0) for r in all_results),
            'results': all_results,
        }
        
        report_result = send_backup_report(api_url, api_key, server_id, organization_id, report)
        
        if report_result.get('status') == 'success':
            print(f"Backup completed successfully")
            print(f"Total files transferred: {report['total_files']}")
            print(f"Total bytes transferred: {report['total_bytes']}")
            print(f"Successful jobs: {report['successful_jobs']}/{report['total_jobs']}")
        else:
            print(f"ERROR: Failed to send backup report: {report_result.get('message', 'Unknown error')}")
        
    except Exception as e:
        print(f"ERROR: Backup runner failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

# SaltStack Integration - Complete Guide

## Overview

OpsPilot now has complete SaltStack integration with:

1. ✅ Salt Master (Docker Compose)
2. ✅ Salt Client (Python wrapper)
3. ✅ Salt Runners (metrics, backups, health)
4. ✅ Auto-install script for minions
5. ✅ Makefile commands for easy management

---

## Quick Start

### 1. Start Salt Master

```bash
cd /Volumes/ashrul/Development/Active/opspilot

# Start infrastructure (PostgreSQL, Redis, Vault)
docker-compose up -d

# Start Salt Master
make salt-up

# Check logs
make salt-logs
```

### 2. Install Salt Minion on Remote Server

```bash
# Interactive mode
make salt-install-minion

# Or directly
bash scripts/install-salt-minion.sh <server_ip> <ssh_user> <ssh_password> <minion_id> [master_ip]

# Examples:
# With password:
bash scripts/install-salt-minion.sh 192.168.1.100 root mypassword webserver1 192.168.1.10

# With SSH key:
bash scripts/install-salt-minion.sh 192.168.1.100 root ~/.ssh/id_ed25519 webserver1
```

### 3. Accept Minion Key

```bash
# List all keys
make salt-keys

# Accept all pending keys
make salt-accept

# Accept specific minion
make salt-accept-minion
# Enter minion ID when prompted

# Test connection
make salt-test
```

### 4. Use Salt from Backend

```python
from app.core.salt import salt_client

# Ping minions
result = await salt_client.ping(target="*")
# Returns: {"minion1": True, "minion2": True}

# Get metrics
metrics = await salt_client.get_metrics(minion_id="minion1")
# Returns: {"cpu_percent": 25.5, "memory_percent": 60.2, ...}

# Run backup
backup_result = await salt_client.run_backup(
    minion_id="minion1",
    backup_config={
        "source": "/var/www/html",
        "destination": "/backup/webserver1",
        "compression": "gzip"
    }
)

# Execute shell command
cmd_result = await salt_client.execute_shell_command(
    minion_id="minion1",
    command="ls -la /var/log"
)
```

---

## Architecture

### Components

1. **Salt Master** (Docker container)
   - Runs on port 4505/4506 (Salt communication)
   - Runs on port 8000 (Salt API)
   - Hosts Salt states and pillars
   - Manages minion authentication

2. **Salt Client** (`backend/app/core/salt.py`)
   - Python wrapper for Salt API
   - Handles authentication
   - Provides async methods for all Salt operations
   - Integrated with FastAPI endpoints

3. **Salt Runners** (`salt/salt/_modules/`)
   - `metrics_collector.py` - Collects CPU, memory, disk, network metrics
   - `backup_runner.py` - Executes rsync backups
   - `health_checker.py` - Performs health checks

4. **Salt States** (`salt/salt/`)
   - Server configuration management
   - Monitoring setup
   - Backup automation
   - Security hardening

5. **Salt Pillars** (`pillar/`)
   - Configuration data for minions
   - Organization-specific settings
   - Environment-specific configs

---

## Makefile Commands

### Salt Management

```bash
# Start Salt Master
make salt-up

# Stop Salt Master
make salt-down

# View logs
make salt-logs
```

### Minion Management

```bash
# List all keys (accepted and pending)
make salt-keys

# Accept all pending keys
make salt-accept

# Accept specific minion (interactive)
make salt-accept-minion

# Ping all minions
make salt-test

# Get grains from all minions
make salt-grains
```

### Minion Installation

```bash
# Interactive installer (prompts for all info)
make salt-install-minion
```

### Salt Operations

```bash
# Run state on minion(s)
make salt-run-state
# Prompts: Target minion, State name

# Execute command on minion(s)
make salt-cmd
# Prompts: Target minion, Command
```

---

## API Endpoints

### Salt API (Backend)

The backend provides these Salt-related endpoints:

- `POST /api/v1/salt/metrics` - Ingest metrics from Salt runner
- `POST /api/v1/salt/backups` - Report backup execution
- `POST /api/v1/salt/health` - Report health checks
- `POST /api/v1/salt/logs` - Ship logs to backend

**Authentication:** These endpoints require `X-API-Key` header (configured in `.env`)

---

## Configuration

### Environment Variables

Add to `.env`:

```env
# Salt API
SALT_API_URL=http://localhost:8000
SALT_API_USERNAME=saltapi
SALT_API_PASSWORD=saltapi
```

### Salt Master Configuration

Salt Master is configured via `docker-compose.salt.yml`:

- **Publish Port:** 4505 (salt master publish)
- **Respond Port:** 4506 (salt master respond)
- **API Port:** 8000 (Salt CherryPy API)
- **Authentication:** PAM (username: `saltapi`, password: `saltapi`)

**⚠️ CHANGE DEFAULT PASSWORDS IN PRODUCTION!**

### Salt Minion Configuration

When installing minions, the script:
1. Detects OS (Ubuntu, Debian, RHEL, CentOS, Fedora)
2. Installs Salt Minion from official repo
3. Configures minion ID and master IP
4. Starts Salt Minion service

---

## Salt Client Methods

### Connection

```python
from app.core.salt import salt_client

# Check authentication
if salt_client.is_authenticated():
    print("Connected to Salt Master")
```

### Minion Management

```python
# List all minions
minions = await salt_client.list_minions()

# Accept pending minion
success = await salt_client.accept_key(minion_id="minion1")

# Delete minion key
success = await salt_client.delete_key(minion_id="minion1")
```

### Operations

```python
# Ping minion
result = await salt_client.ping(target="minion1")

# Get grains
grains = await salt_client.get_grains(target="minion1")

# Get metrics
metrics = await salt_client.get_metrics(minion_id="minion1")

# Run backup
backup_result = await salt_client.run_backup(
    minion_id="minion1",
    backup_config={...}
)

# Check health
health = await salt_client.check_health(minion_id="minion1")

# Apply state
state_result = await salt_client.apply_state(
    minion_id="minion1",
    state="opspilot.monitoring",
    test=False
)

# Execute shell command
cmd_result = await salt_client.execute_shell_command(
    minion_id="minion1",
    command="systemctl restart nginx"
)
```

---

## Salt Runners

### Metrics Collector

```python
# Collects from /salt/salt/_modules/metrics_collector.py

result = await salt_client.get_metrics(minion_id="minion1")
# Returns:
# {
#     "cpu_percent": 25.5,
#     "cpu_count": 4,
#     "memory_percent": 60.2,
#     "memory_used_gb": 4.8,
#     "memory_total_gb": 8.0,
#     "disk_usage_percent": 45.3,
#     "disk_used_gb": 90.6,
#     "disk_total_gb": 200.0,
#     "network_in_bps": 1024000,
#     "network_out_bps": 512000,
#     "uptime_seconds": 1234567
# }
```

### Backup Runner

```python
# Executes from /salt/salt/_modules/backup_runner.py

backup_result = await salt_client.run_backup(
    minion_id="minion1",
    backup_config={
        "source": "/var/www/html",
        "destination": "/backup/webserver1",
        "compression": "gzip",
        "exclude": ["/tmp/*", "*.log"]
    }
)
# Returns:
# {
#     "status": "completed",
#     "duration_seconds": 300,
#     "files_transferred": 1250,
#     "bytes_transferred": 524288000,
#     "checksum": "abc123..."
# }
```

### Health Checker

```python
# Executes from /salt/salt/_modules/health_checker.py

health = await salt_client.check_health(minion_id="minion1")
# Returns:
# {
#     "services": {
#         "nginx": {"status": "running", "uptime": 12345},
#         "mysql": {"status": "running", "uptime": 67890},
#         "redis": {"status": "stopped", "uptime": 0}
#     },
#     "disk": {"status": "ok", "usage_percent": 45.3},
#     "memory": {"status": "ok", "usage_percent": 60.2}
# }
```

---

## Troubleshooting

### Salt Master won't start

```bash
# Check logs
make salt-logs

# Check container status
docker ps | grep salt

# Restart Salt Master
docker-compose -f docker-compose.salt.yml restart
```

### Minion can't connect to master

```bash
# On minion server:
sudo systemctl status salt-minion
sudo journalctl -u salt-minion -n 50

# Check minion config
cat /etc/salt/minion

# Test connectivity
ping <master_ip>
telnet <master_ip> 4505
```

### Salt API authentication fails

```bash
# Check Salt API is running
curl http://localhost:8000

# Test authentication manually
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "saltapi", "password": "saltapi", "eauth": "pam"}'

# Check Salt Master logs
make salt-logs
```

### Minion key not accepted

```bash
# List keys on master
make salt-keys

# Check if minion is trying to connect
# On minion: sudo salt-minion -l debug

# Manually accept key
docker-compose -f docker-compose.salt.yml exec salt-master salt-key -a <minion_id>

# Delete and re-accept
docker-compose -f docker-compose.salt.yml exec salt-master salt-key -d <minion_id>
```

### Salt command timeout

```bash
# Increase timeout in Salt Client
# Edit app/core/salt.py, increase timeout parameter

# Test specific command
docker-compose -f docker-compose.salt.yml exec salt-master salt 'minion1' test.ping -t 30
```

---

## Security Best Practices

### Production Deployment

1. **Change default credentials:**
   - Update `SALT_API_USERNAME` and `SALT_API_PASSWORD` in `.env`
   - Use strong, random passwords

2. **Enable TLS:**
   - Configure SSL certificates for Salt API
   - Update `docker-compose.salt.yml` with cert paths

3. **Network security:**
   - Use firewall rules to limit Salt ports (4505, 4506, 8000)
   - Only allow minion IPs to connect

4. **Key management:**
   - Use Vault to store Salt API credentials
   - Rotate keys regularly
   - Use separate credentials for dev/staging/prod

5. **Minion isolation:**
   - Use separate master for different environments
   - Implement proper key acceptance workflows
   - Use minions' grains for access control

---

## Next Steps

### Immediate

1. ✅ Start Salt Master: `make salt-up`
2. ✅ Install first minion: `make salt-install-minion`
3. ✅ Test connection: `make salt-test`

### Integration

1. Connect Salt Client to backend endpoints
2. Implement metrics ingestion schedule
3. Set up backup automation
4. Configure health check intervals

### Advanced

1. Create custom Salt states for your infrastructure
2. Implement Salt reactor for real-time events
3. Set up Salt syndic for multi-master
4. Configure Salt Cloud for cloud provisioning

---

## Documentation

- [SaltStack Official Docs](https://docs.saltproject.io/)
- [Salt API Documentation](https://docs.saltproject.io/en/latest/ref/netapi/all/salt.netapi.rest_cherrypy.html)
- [OpsPilot PRD](/Volumes/ashrul/Development/Active/prds/current/2026-Q2/)

---

## Support

For issues or questions:
1. Check Salt logs: `make salt-logs`
2. Review backend logs for API errors
3. Test Salt API directly with curl
4. Check minion logs on target server

---

**SaltStack Integration Complete!** 🧂✅

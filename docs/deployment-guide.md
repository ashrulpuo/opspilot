# SaltStack Data Collection - Deployment Guide

## Overview

This guide covers deploying the SaltStack Data Collection feature in a production environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Salt Minion Installation](#salt-minion-installation)
- [Configuration](#configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Software Requirements

- **Python:** 3.11 or higher
- **Node.js:** 18 or higher
- **PostgreSQL:** 15 or higher
- **TimescaleDB:** 2.11 or higher
- **Redis:** 7 or higher
- **Salt:** 3006 or higher (on managed servers)

### Hardware Requirements

**Minimum:**
- **CPU:** 2 cores
- **RAM:** 4GB
- **Disk:** 50GB SSD
- **Network:** 100 Mbps

**Recommended:**
- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Disk:** 100GB+ SSD
- **Network:** 1 Gbps

### External Services

- **SMTP Server:** For email notifications (optional)
- **Object Storage:** For backups (optional)
- **DNS Server:** For domain resolution (optional)

---

## Infrastructure Setup

### Server Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Load Balancer (Optional)             │
│                   (Nginx, HAProxy)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼────┐ ┌────▼────┐ ┌────▼────┐
│   Backend   │ │ Frontend │ │  Redis   │
│   API      │ │  (Vue)   │ │  Server  │
│   (FastAPI) │ │          │ │          │
└───────┬────┘ └────┬────┘ └────┬────┘
        │            │             │
        └────────────┼─────────────┘
                     │
        ┌────────────▼─────────────┐
        │   PostgreSQL + TimescaleDB │
        │          (Database)       │
        └───────────────────────────┘
```

### Network Configuration

**Required Ports:**
- **Backend API:** 8000 (HTTP)
- **Backend SSE:** 8000 (HTTP)
- **PostgreSQL:** 5432
- **Redis:** 6379
- **Salt Master:** 4505/4506 (if using master)

**Firewall Rules:**
```bash
# Backend API
sudo ufw allow 8000/tcp

# PostgreSQL (only from backend server)
sudo ufw allow from 10.0.0.0/24 to any port 5432

# Redis (only from backend server)
sudo ufw allow from 10.0.0.0/24 to any port 6379
```

---

## Backend Deployment

### 1. Clone Repository

```bash
cd /opt
git clone https://github.com/your-org/opspilot.git
cd opspilot/backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file:

```bash
# Application
APP_NAME=ops-pilot
APP_ENV=production
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/opspilot
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=50

# Salt
SALT_MASTER_HOST=localhost
SALT_MASTER_PORT=4506
SALT_API_USER=saltapi
SALT_API_PASSWORD=saltapipassword

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 5. Run Database Migrations

```bash
# Initialize TimescaleDB
psql -U postgres -d opspilot -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run migrations
alembic upgrade head
```

### 6. Create Systemd Service

Create `/etc/systemd/system/opspilot-backend.service`:

```ini
[Unit]
Description=OpsPilot Backend
After=network.target postgresql.service redis.service

[Service]
User=opspilot
Group=opspilot
WorkingDirectory=/opt/opspilot/backend
Environment="PATH=/opt/opspilot/backend/venv/bin"
ExecStart=/opt/opspilot/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable opspilot-backend
sudo systemctl start opspilot-backend
sudo systemctl status opspilot-backend
```

### 7. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/opspilot`:

```nginx
upstream opspilot_backend {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://opspilot_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # SSE-specific headers
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering no;
    }

    location /docs {
        proxy_pass http://opspilot_backend;
    }

    location /openapi.json {
        proxy_pass http://opspilot_backend;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/opspilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Configure SSL (HTTPS)

Use Let's Encrypt:

```bash
sudo certbot --nginx -d api.yourdomain.com
```

---

## Frontend Deployment

### 1. Clone Repository

```bash
cd /var/www
git clone https://github.com/your-org/opspilot-frontend.git frontend
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

Create `.env.production`:

```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_APP_TITLE=OpsPilot
VITE_APP_VERSION=1.0.0
```

### 4. Build Frontend

```bash
npm run build
```

### 5. Configure Nginx

Create `/etc/nginx/sites-available/opspilot-frontend`:

```nginx
server {
    listen 80;
    server_name app.yourdomain.com;

    root /var/www/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/opspilot-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Configure SSL

```bash
sudo certbot --nginx -d app.yourdomain.com
```

---

## Salt Minion Installation

### 1. Install Salt on Managed Servers

**Debian/Ubuntu:**

```bash
wget -O - https://repo.saltproject.io/salt/py3/ubuntu/22.04/amd64/latest/salt-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/salt-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/salt-archive-keyring.gpg] https://repo.saltproject.io/salt/py3/ubuntu/22.04/amd64/latest jammy main" | tee /etc/apt/sources.list.d/salt.list
apt update
apt install -y salt-minion
```

**RHEL/CentOS:**

```bash
yum install -y https://repo.saltproject.io/salt/py3/redhat/8/x86_64/latest/salt-repo-latest.el8.noarch.rpm
yum install -y salt-minion
```

### 2. Configure Minion

Edit `/etc/salt/minion`:

```ini
# Minion ID (auto-generated or specify)
id: server-hostname

# OpsPilot backend
master: 127.0.0.1  # Salt master IP or hostname
master_port: 4506

# Enable beacons
beacons:
  disk_usage:
    interval: 60
  service_status:
    interval: 60
  load:
    interval: 60
  mem:
    interval: 60
  pkg:
    interval: 300

# Enable Salt API
user: saltapi
publisher_acl:
  saltapi:
    - .*  # Allow all commands
```

### 3. Start Minion Service

```bash
systemctl enable salt-minion
systemctl start salt-minion
systemctl status salt-minion
```

### 4. Verify Registration

```bash
# On the Salt master
salt-key -L

# Accept minion
salt-key -A minion-id

# Test communication
salt minion-id test.ping
```

---

## Configuration

### Database Configuration

**TimescaleDB Retention Policies:**

```sql
-- 90-day retention for metrics
SELECT add_retention_policy('metrics', INTERVAL '90 days');

-- 365-day retention for events
SELECT add_retention_policy('salt_events', INTERVAL '365 days');

-- 90-day retention for logs
SELECT add_retention_policy('salt_logs', INTERVAL '90 days');
```

**Connection Pooling:**

```python
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_TIMEOUT = 30
```

### Redis Configuration

Edit `/etc/redis/redis.conf`:

```ini
# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
timeout 300
tcp-keepalive 60
```

Restart Redis:

```bash
sudo systemctl restart redis
```

### SSE Configuration

**Backend Settings:**

```python
# SSE settings
SSE_KEEPALIVE_INTERVAL = 15  # seconds
SSE_RETRY_INTERVAL = 5  # seconds
SSE_MAX_CONNECTIONS = 1000
```

**Frontend Settings:**

```typescript
// SSE reconnection settings
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY_BASE = 5000  // 5s
const RECONNECT_DELAY_MAX = 60000  // 60s
```

### Monitoring Configuration

**Alert Thresholds:**

```yaml
alerts:
  cpu:
    warning: 70
    critical: 90
  memory:
    warning: 70
    critical: 90
  disk:
    warning: 80
    critical: 95
  load:
    warning: 2.0
    critical: 4.0
```

---

## Monitoring and Maintenance

### Health Checks

**Backend Health:**

```bash
# Check SSE health
curl https://api.yourdomain.com/api/v1/stream/health

# Check API health
curl https://api.yourdomain.com/api/health

# Check database connectivity
psql -U postgres -d opspilot -c "SELECT 1;"

# Check Redis connectivity
redis-cli ping
```

### Log Monitoring

**Backend Logs:**

```bash
# View backend logs
sudo journalctl -u opspilot-backend -f

# View error logs only
sudo journalctl -u opspilot-backend -p err -f

# View last 100 lines
sudo journalctl -u opspilot-backend -n 100
```

**Salt Minion Logs:**

```bash
# View minion logs
sudo journalctl -u salt-minion -f
```

**Nginx Logs:**

```bash
# Access logs
sudo tail -f /var/log/nginx/opspilot-access.log

# Error logs
sudo tail -f /var/log/nginx/opspilot-error.log
```

### Performance Monitoring

**Database Performance:**

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check query performance
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

**Redis Performance:**

```bash
# Check memory usage
redis-cli INFO memory

# Check connections
redis-cli INFO clients

# Check slow log
redis-cli SLOWLOG GET 10
```

### Backup Procedures

**Database Backup:**

```bash
# Daily backup script
pg_dump -U postgres opspilot | gzip > /backup/opspilot_$(date +%Y%m%d).sql.gz

# Keep last 30 days
find /backup -name "opspilot_*.sql.gz" -mtime +30 -delete
```

**Configuration Backup:**

```bash
# Backup environment files
tar -czf /backup/env_$(date +%Y%m%d).tar.gz /opt/opspilot/backend/.env

# Backup Salt configuration
tar -czf /backup/salt_config_$(date +%Y%m%d).tar.gz /etc/salt
```

**Salt Minion Backup:**

```bash
# Backup minion configuration
tar -czf /backup/salt_minion_$(date +%Y%m%d).tar.gz /etc/salt/minion
```

### Maintenance Tasks

**Weekly:**
- Review system logs for errors
- Check disk space usage
- Review alert history
- Update Salt minions if needed

**Monthly:**
- Review database performance
- Optimize database tables
- Review Redis memory usage
- Review user permissions
- Test backup restoration

**Quarterly:**
- Review security patches
- Update TLS certificates
- Review and update alert thresholds
- Performance tuning

---

## Troubleshooting

### Backend Issues

**Backend won't start:**

```bash
# Check service status
sudo systemctl status opspilot-backend

# Check logs
sudo journalctl -u opspilot-backend -n 100

# Check port conflicts
sudo netstat -tulpn | grep 8000

# Check database connectivity
psql -U postgres -d opspilot -c "SELECT 1;"
```

**SSE connections dropping:**

```bash
# Check Redis connection
redis-cli ping

# Check Redis memory
redis-cli INFO memory

# Check SSE logs
sudo journalctl -u opspilot-backend | grep SSE

# Check client-side console for errors
# Browser DevTools → Console
```

**Database connection errors:**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test connection
psql -U postgres -h localhost -d opspilot
```

### Frontend Issues

**Build fails:**

```bash
# Clear cache
rm -rf node_modules/.vite

# Reinstall dependencies
rm -rf node_modules
npm install

# Check Node.js version
node --version  # Should be 18+
```

**SSE not connecting:**

```bash
# Check backend API is accessible
curl https://api.yourdomain.com/api/v1/stream/health

# Check JWT token validity
# Browser DevTools → Application → Local Storage

# Check CORS configuration
# Browser DevTools → Network → Headers
```

### Salt Minion Issues

**Minion won't start:**

```bash
# Check service status
sudo systemctl status salt-minion

# Check configuration
salt-minion --test-config

# Check logs
sudo journalctl -u salt-minion -f
```

**Minion can't connect to master:**

```bash
# Test connectivity
telnet master-host 4506

# Check DNS resolution
nslookup master-host

# Check firewall rules
sudo ufw status
```

**Beacons not working:**

```bash
# Test beacon configuration
salt-call beacon.list

# Run beacon manually
salt-call beacon.disk_usage

# Check beacon logs
sudo journalctl -u salt-minion | grep beacon
```

### Performance Issues

**Slow database queries:**

```sql
-- Identify slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Add indexes if needed
CREATE INDEX idx_metrics_server_id_timestamp ON metrics(server_id, timestamp);
```

**High memory usage:**

```bash
# Check Python memory usage
ps aux | grep uvicorn

# Reduce worker count
# Update systemd service: --workers 2

# Check connection pool
ps aux | grep postgres
```

**Slow SSE streaming:**

```bash
# Check Redis performance
redis-cli INFO stats

# Increase Redis memory
# Update redis.conf: maxmemory 4gb

# Optimize SSE message size
# Reduce metadata in messages
```

---

## Security Best Practices

### Authentication

- Use strong JWT secrets (32+ characters)
- Rotate JWT secrets regularly
- Set short token expiration times (30 minutes)
- Implement refresh token mechanism

### Authorization

- Implement RBAC (Role-Based Access Control)
- Restrict server access to authorized users
- Use least privilege principle
- Regularly review user permissions

### Network Security

- Use TLS/HTTPS for all connections
- Implement firewall rules
- Use VPN for admin access
- Disable direct database access from internet

### Data Security

- Encrypt sensitive data at rest
- Use environment variables for secrets
- Never commit secrets to version control
- Implement data retention policies

### Monitoring

- Monitor for suspicious activity
- Set up alerting for security events
- Regularly audit access logs
- Implement intrusion detection

---

## Scaling Considerations

### Horizontal Scaling

**Backend:**
- Add more backend servers behind load balancer
- Use sticky sessions for SSE connections
- Use shared Redis instance for pub/sub
- Use shared PostgreSQL with read replicas

**Frontend:**
- Serve from CDN for static assets
- Use multiple web servers behind load balancer
- Implement browser caching

### Vertical Scaling

**Database:**
- Increase database server resources
- Optimize queries and indexes
- Use read replicas for reporting
- Partition large tables

**Redis:**
- Use Redis Cluster for large deployments
- Increase memory allocation
- Optimize data structures

---

## Disaster Recovery

### Backup Strategy

- **Database:** Daily backups with 30-day retention
- **Configuration:** Version control + automated backups
- **Salt States:** Repository + backups
- **Logs:** Centralized log aggregation

### Recovery Procedures

1. **Restore Database:**
   ```bash
   gunzip /backup/opspilot_20260417.sql.gz | psql -U postgres opspilot
   ```

2. **Restore Configuration:**
   ```bash
   tar -xzf /backup/env_20260417.tar.gz -C /opt/opspilot/backend/
   ```

3. **Restore Salt States:**
   ```bash
   git clone https://github.com/your-org/salt-states
   ```

### Testing Recovery

- Test backup restoration monthly
- Document recovery procedures
- Train team on disaster recovery
- Run tabletop exercises

---

## Additional Resources

- **SaltStack Documentation:** https://docs.saltproject.io/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Vue.js Documentation:** https://vuejs.org/
- **TimescaleDB Documentation:** https://docs.timescale.com/
- **Nginx Documentation:** https://nginx.org/en/docs/

---

**Last Updated:** 2026-04-17
**Version:** 1.0.0

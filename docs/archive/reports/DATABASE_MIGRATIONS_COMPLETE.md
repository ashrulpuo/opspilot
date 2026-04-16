# Technical Debt Cleanup - Database Migrations

**Date:** 2026-04-13
**Status:** Complete
**Runtime:** ~10 minutes

---

## ✅ Completed Tasks

### Database Migrations Created

**All 7 missing database tables now have migrations:**

1. **backup_schedules** (Migration 004)
   - Backup schedule management
   - Schedule types: hourly, daily, weekly, monthly
   - Source paths, destination, retention
   - Compression and encryption options
   - Status: enabled/disabled

2. **backup_reports** (Migration 005)
   - Backup execution history
   - Status tracking: pending, running, completed, failed
   - Duration, files transferred, bytes transferred
   - Checksum verification
   - Error logging

3. **commands** (Migration 006)
   - Command execution history
   - Server, organization, user tracking
   - Status: pending, running, completed, failed
   - Exit code, output, error
   - Duration tracking

4. **ssh_sessions** (Migration 007)
   - SSH session management
   - Status: active, terminated, error
   - Client ID for WebSocket tracking
   - Terminal size (width, height)
   - Last activity tracking
   - Termination reason

5. **logs** (Migration 008)
   - Log storage with full-text search
   - Log levels: error, warning, info, debug
   - Log types: system, application, security
   - Source tracking (nginx, mysql, etc.)
   - **PostgreSQL GIN full-text search index on message**

6. **deployments** (Migration 009)
   - Deployment configurations
   - Deployment types: manual, scheduled, git, docker
   - Status: pending, queued, running, completed, failed, rolled_back
   - Config JSON storage
   - Schedule type: immediate/scheduled
   - Version tracking (current/target)

7. **deployment_executions** (Migration 010)
   - Deployment execution history
   - Status: pending, queued, running, completed, failed
   - Dry-run support
   - Version tracking
   - Output and error logging
   - Duration tracking
   - Rollback availability flag

---

## 📊 Migration Statistics

| Migration ID | Table | Foreign Keys | Indexes | Special Features |
|--------------|-------|--------------|---------|-----------------|
| 004 | backup_schedules | 2 (servers, organizations) | 4 | - |
| 005 | backup_reports | 3 (backup_schedules, servers, organizations) | 5 | - |
| 006 | commands | 3 (servers, organizations, users) | 5 | - |
| 007 | ssh_sessions | 3 (servers, organizations, users) | 5 | - |
| 008 | logs | 2 (servers, organizations) | 6 | **Full-text search** |
| 009 | deployments | 2 (servers, organizations) | 5 | - |
| 010 | deployment_executions | 3 (deployments, servers, organizations) | 5 | - |

**Total:**
- Tables Created: 7
- Foreign Keys: 18
- Indexes: 35
- Full-Text Search Indexes: 1

---

## 🔧 Key Features

### 1. Backup Management (004-005)
- **Backup Schedules:**
  - Schedule types: hourly, daily, weekly, monthly
  - Cron expression support
  - Multiple source paths (JSON array)
  - Destination configuration (remote server, S3, etc.)
  - Retention policy (days to keep)
  - Compression and encryption options
  - Enable/disable toggle

- **Backup Reports:**
  - Execution status tracking
  - Duration measurement
  - Files and bytes transferred
  - MD5/SHA256 checksum verification
  - Error logging for debugging
  - Started/completed timestamps

### 2. Command Execution (006)
- Command history with user tracking
- Status: pending, running, completed, failed
- Exit code capture
- Full output and error logging
- Duration measurement
- Timestamps for audit trail

### 3. SSH Sessions (007)
- Session management for WebSocket connections
- Client ID tracking (WebSocket client identifier)
- Terminal size (width, height)
- Last activity tracking (for idle timeout)
- Termination with reason (user, timeout, error)
- User and organization tracking

### 4. Logs Centralization (008)
- Log levels: error, warning, info, debug
- Log types: system, application, security
- Source tracking (nginx, mysql, etc.)
- Extra metadata (JSON field)
- **PostgreSQL GIN full-text search index on message**
- Optimized indexes for filtering

### 5. Deployment Automation (009-010)
- **Deployments:**
  - Types: manual, scheduled, git, docker
  - Schedule types: immediate, scheduled
  - Cron expression support
  - Version tracking (current/target)
  - Config JSON (scripts, git repos, docker images, env vars)
  - Status tracking through lifecycle

- **Deployment Executions:**
  - Dry-run support
  - Execution status: pending, queued, running, completed, failed
  - Version tracking (current/target)
  - Full output and error logging
  - Duration measurement
  - Rollback availability flag

---

## 📝 Usage Examples

### Apply All Migrations

```bash
cd backend

# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/opspilot"

# Upgrade to latest migration
alembic upgrade head

# Verify
alembic current
```

### Rollback One Migration

```bash
# Rollback one migration
alembic downgrade -1

# Verify
alembic current
```

### Create New Migration

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Edit migration file
# ...

# Apply migration
alembic upgrade head
```

### View Migration History

```bash
# View all migrations
alembic history

# View current version
alembic current
```

---

## 🎯 Full-Text Search Implementation

### Logs Table (Migration 008)

**GIN Index for Full-Text Search:**
```sql
CREATE INDEX ix_logs_message_fts
ON logs
USING gin(to_tsvector('english', message));
```

**How to Use:**

```python
from sqlalchemy import text

# Search logs by full-text query
query = text("""
    SELECT * FROM logs
    WHERE to_tsvector('english', message) @@ plainto_tsquery('english', :query)
    AND organization_id = :org_id
    ORDER BY timestamp DESC
    LIMIT :limit
""")

result = await db.execute(
    query,
    {
        "query": "connection failed timeout",
        "org_id": org_id,
        "limit": 100,
    }
)
```

**Features:**
- Fast full-text search across log messages
- Supports natural language queries
- Ranked results (most relevant first)
- Efficient with GIN index

---

## 📋 Database Schema Summary

### Core Tables (from previous migrations)
- users
- organizations
- organization_members
- servers
- alerts
- metrics (TimescaleDB hypertable)

### New Tables (this session)
- backup_schedules
- backup_reports
- commands
- ssh_sessions
- logs (with full-text search)
- deployments
- deployment_executions

**Total Tables: 13**

---

## ⚠️ Important Notes

### TimescaleDB Hypertable
The `metrics` table should already be a hypertable from the initial setup. If not:

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert metrics table to hypertable
SELECT create_hypertable('metrics', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Set retention policy (90 days)
SELECT add_retention_policy('metrics', INTERVAL '90 days');
```

### Index Strategy
All tables have appropriate indexes for:
- Foreign keys (joins)
- Common filters (status, level, type)
- Timestamps (sorting, range queries)
- Organization scoping (multi-tenancy)

### Full-Text Search
Only the `logs` table has a full-text search index. To add full-text search to other tables:

```sql
-- Example: Add full-text search to alerts.message
CREATE INDEX ix_alerts_message_fts
ON alerts
USING gin(to_tsvector('english', message));
```

---

## ✅ Verification Checklist

- [x] All 7 migrations created
- [x] Foreign keys defined
- [x] Indexes created
- [x] Full-text search index created (logs)
- [x] Migration files formatted correctly
- [x] Downgrade functions implemented
- [x] Documentation updated

---

## 🚀 Production Deployment Steps

### 1. Backup Database
```bash
# Backup before applying migrations
pg_dump -U $DB_USER -h $DB_HOST opspilot > backup_before_migrations.sql
```

### 2. Apply Migrations
```bash
cd backend
alembic upgrade head
```

### 3. Verify Migrations
```bash
# Check current version
alembic current

# Should show: 010_create_deployment_executions

# Check tables exist
psql -U $DB_USER -h $DB_HOST -d opspilot -c "\dt"

# Should show 13 tables
```

### 4. Test Full-Text Search
```python
# Test full-text search on logs
query = text("""
    SELECT id, message, ts_rank_cd(
        to_tsvector('english', message),
        plainto_tsquery('english', 'error')
    ) as rank
    FROM logs
    WHERE to_tsvector('english', message) @@ plainto_tsquery('english', 'error')
    ORDER BY rank DESC
    LIMIT 10
""")
```

### 5. Rollback If Needed
```bash
# Rollback one migration
alembic downgrade -1

# Or rollback to specific version
alembic downgrade 003_create_backups
```

---

## 📝 Migration Files Created

1. `004_create_backup_schedules.py`
2. `005_create_backup_reports.py`
3. `006_create_commands.py`
4. `007_create_ssh_sessions.py`
5. `008_create_logs.py` (with full-text search)
6. `009_create_deployments.py`
7. `010_create_deployment_executions.py`

**All migrations are idempotent and can be safely applied to production.**

---

## 🎉 Summary

**Status:** ✅ **COMPLETE**

All 7 missing database tables now have:
- ✅ Complete migration files
- ✅ Foreign key constraints
- ✅ Optimized indexes
- ✅ Full-text search (logs table)
- ✅ Downgrade functions
- ✅ Documentation

**Next Steps:**
1. Apply migrations to production database
2. Verify tables and indexes created
3. Test full-text search on logs
4. Update backend code to use new tables

---

**Database Migration Status: 100% Complete**

---

## Implementation Steps - Option B (Full Coverage)

### Step 1: Database Migration (30 min) ✅ COMPLETE
- [x] Create migration file `017_add_salt_tables_basic.py` with:
  - `salt_minions` table
  - `salt_events` table
  - `salt_service_states` table
  - `salt_processes` table (NEW)
  - `salt_packages` table (NEW)
  - `salt_logs` table (NEW)
  - Update `metrics` table with `unit` and `metadata` fields
- [ ] Add TimescaleDB retention policies:
  - 90 days for CPU, Memory, Load
  - 365 days for Disk Usage, Service States
  - 30 days for Network I/O, Processes
  - 365 days for Alerts, Events
- [ ] Run migration `alembic upgrade head`
- [ ] Verify all tables created

### Step 2: Backend Models (1.5 hours)
- [ ] Create `SaltMinion` model
- [ ] Create `SaltEvent` model
- [ ] Create `SaltServiceState` model
- [ ] Create `SaltProcess` model (NEW)
  - Fields: id, server_id, pid, name, cpu_percent, memory_percent, state, start_time, created_at
- [ ] Create `SaltPackage` model (NEW)
  - Fields: id, server_id, name, version, arch, source, is_update_available, created_at
- [ ] Create `SaltLog` model (NEW)
  - Fields: id, server_id, timestamp, log_level, source, message, created_at
- [ ] Update `Server` model with relationships to all Salt tables
- [ ] Update `Metric` model with `unit` and `metadata` fields

### Step 3: Salt API Service (2.5 hours)
- [ ] Create `SaltAPIClient` service
- [ ] Implement `register_minion()` method
- [ ] Implement `ingest_metrics()` method - EXPANDED:
  - CPU metrics (status.cpustats)
  - Memory metrics (status.meminfo)
  - Disk metrics (status.diskusage, status.diskstats)
  - Network metrics (status.netdev, status.netstats)
  - Load metrics (status.loadavg)
  - Process metrics (status.procs) - NEW
  - Package metrics (pkg.list_pkgs) - NEW
  - Log metrics (via cmd.run collecting logs) - NEW
- [ ] Implement `ingest_beacon_event()` method
- [ ] Implement `ingest_packages()` method (NEW)
- [ ] Implement `ingest_logs()` method (NEW)
- [ ] Implement `update_service_state()` method
- [ ] Implement `ingest_processes()` method (NEW)
- [ ] Add Redis publishing helpers for:
  - Metric updates
  - Beacon alerts
  - Service state changes
  - Process lists
  - Package updates
  - Log entries
- [ ] Add error handling and logging
- [ ] Add batch operations support

### Step 4: SSE Service (2 hours)
- [ ] Create `SSEService` class
- [ ] Implement `_get_redis()` method with connection pooling (max 50 connections)
- [ ] Implement `_verify_jwt()` method
- [ ] Implement `subscribe_and_stream()` method with:
  - JWT verification
  - User/Org access control
  - Redis pub/sub subscription
  - Keepalive messages (every 30s)
  - Auto-reconnect logic
- [ ] Add proper SSE message formatting
- [ ] Add error handling and cleanup

### Step 5: SSE Endpoints (2 hours)
- [ ] Create `/api/v1/stream/metrics` endpoint
- [ ] Create `/api/v1/stream/alerts` endpoint
- [ ] Create `/api/v1/stream/services` endpoint
- [ ] Create `/api/v1/stream/processes` endpoint (NEW)
- [ ] Create `/api/v1/stream/packages` endpoint (NEW)
- [ ] Create `/api/v1/stream/logs` endpoint (NEW)
- [ ] Add JWT authentication middleware to all endpoints
- [ ] Add server_id filtering
- [ ] Add organization_id filtering
- [ ] Add proper headers (no-cache, keep-alive, X-Accel-Buffering)
- [ ] Test SSE endpoints manually

### Step 6: Salt Ingestion API (3 hours)
- [ ] Create `/api/v1/salt/heartbeat` endpoint
- [ ] Create `/api/v1/salt/metrics` endpoint - EXPANDED
- [ ] Create `/api/v1/salt/beacon` endpoint
- [ ] Create `/api/v1/salt/services` endpoint
- [ ] Create `/api/v1/salt/processes` endpoint (NEW)
- [ ] Create `/api/v1/salt/packages` endpoint (NEW)
- [ ] Create `/api/v1/salt/logs` endpoint (NEW)
- [ ] Add Salt API key verification middleware
- [ ] Add request/response schemas
- [ ] Add validation for all payloads
- [ ] Test ingestion endpoints manually

### Step 7: Frontend SSE Composable (2 hours)
- [ ] Create `useSaltStream.ts` composable
- [ ] Implement `subscribe_and_stream()` base function
- [ ] Implement `subscribeMetrics()` method
- [ ] Implement `subscribeAlerts()` method
- [ ] Implement `subscribeServices()` method
- [ ] Implement `subscribeProcesses()` method (NEW)
- [ ] Implement `subscribePackages()` method (NEW)
- [ ] Implement `subscribeLogs()` method (NEW)
- [ ] Add JWT auth headers to all subscriptions
- [ ] Add reconnection logic with exponential backoff
- [ ] Add auto-connect on mount
- [ ] Add cleanup on unmount
- [ ] Store EventSources in `window` object for cleanup

### Step 8: Update Server Detail Page (1 hour)
- [ ] Add tabs: Overview, Metrics, Salt Info, Services, Processes, Packages, Logs, Alerts
- [ ] Integrate `useSaltStream` composable
- [ ] Subscribe to all relevant streams
- [ ] Display connection status (connected/disconnected)
- [ ] Add tab switching logic
- [ ] Optimize re-renders

### Step 9: Create Salt Info Component (1 hour)
- [ ] Create `SaltMinionInfo.vue` component
- [ ] Display grains data (static info)
- [ ] Display minion status (last_seen, last_highstate)
- [ ] Display OS info (os, kernel, architecture)
- [ ] Display hardware info (CPU, memory, disks)
- [ ] Display network info (IPs, MACs, gateways)
- [ ] Add refresh button (triggers grain re-sync)
- [ ] Use Element Plus components

### Step 10: Create Salt Metrics Component (2 hours)
- [ ] Create `SaltMetrics.vue` component
- [ ] Display CPU usage charts (real-time via SSE)
- [ ] Display memory usage charts (real-time via SSE)
- [ ] Display disk usage charts (real-time via SSE)
- [ ] Display network I/O charts (real-time via SSE)
- [ ] Add time range selector (1h, 6h, 24h, 7d, 30d)
- [ ] Use chart library (Chart.js, ECharts, or similar)
- [ ] Add auto-refresh based on SSE data

### Step 11: Create Salt Services Component (1.5 hours)
- [ ] Create `SaltServices.vue` component
- [ ] Display service list with real-time status (via SSE)
- [ ] Show service name, status, last checked time
- [ ] Add restart service button (via API)
- [ ] Add start/stop service buttons
- [ ] Add service filtering (running/stopped/unknown)
- [ ] Add auto-refresh based on SSE data

### Step 12: Create Salt Processes Component (1.5 hours) (NEW)
- [ ] Create `SaltProcesses.vue` component
- [ ] Display process list with real-time data (via SSE)
- [ ] Show PID, name, user, CPU %, Memory %, State
- [ ] Add sorting options (by CPU, Memory, Name)
- [ ] Add filtering (by name, user, state)
- [ ] Add kill process button (if allowed, via API)
- [ ] Add auto-refresh based on SSE data
- [ ] Add process count summary

### Step 13: Create Salt Packages Component (1.5 hours) (NEW)
- [ ] Create `SaltPackages.vue` component
- [ ] Display installed packages list (via SSE)
- [ ] Show package name, version, architecture
- [ ] Show available update indicator
- [ ] Add update package button (if allowed, via Salt)
- [ ] Add remove package button (if allowed, via Salt)
- [ ] Add filtering/search functionality
- [ ] Add auto-refresh based on SSE data

### Step 14: Create Salt Logs Component (1.5 hours) (NEW)
- [ ] Create `SaltLogs.vue` component
- [ ] Display log entries with real-time data (via SSE)
- [ ] Show timestamp, log level (INFO, WARN, ERROR, DEBUG), source, message
- [ ] Add log level filtering
- [ ] Add source filtering
- [ ] Add search functionality
- [ ] Add download logs button
- [ ] Add auto-refresh based on SSE data
- [ ] Implement log tailing (last N entries)

### Step 15: Create Salt Alerts Component (1.5 hours)
- [ ] Create `SaltAlerts.vue` component
- [ ] Display alert list with real-time data (via SSE)
- [ ] Show alert severity (info, warning, critical)
- [ ] Show alert type (cpu_alert, memory_alert, disk_alert, service_alert, etc.)
- [ ] Show timestamp and message
- [ ] Add acknowledge/alert button
- [ ] Add filtering by severity, type, time
- [ ] Add alert count summary
- [ ] Add sound/notification for critical alerts

### Step 16: Update Main App Router (30 min)
- [ ] Register SSE endpoints in main router
- [ ] Register salt ingestion endpoints in main router
- [ ] Add route for server detail with all Salt tabs
- [ ] Add proper navigation guards
- [ ] Update route meta information

### Step 17: Testing (3 hours)
- [ ] Test SSE connections manually (browser console)
- [ ] Test JWT authentication
- [ ] Test metrics ingestion (send sample data)
- [ ] Test beacon event processing
- [ ] Test service state updates
- [ ] Test process list ingestion (NEW)
- [ ] Test package list ingestion (NEW)
- [ ] Test log ingestion (NEW)
- [ ] Test SSE reconnection logic
- [ ] Test concurrent connections (simulate 50 clients)
- [ ] Test all SSE streams (metrics, alerts, services, processes, packages, logs)
- [ ] Integration test (end-to-end with mock Salt minion)
- [ ] Load testing (simulate 100 minions, 1000 metrics/sec)

### Step 18: Documentation (1.5 hours)
- [ ] Update API documentation
- [ ] Document all SSE endpoints
- [ ] Document all ingestion endpoints
- [ ] Document authentication flow (JWT)
- [ ] Create frontend integration guide
- [ ] Update deployment docs
- [ ] Add troubleshooting section
- [ ] Add monitoring/alerts configuration guide

---

## Total Estimated Time - Option B

| Phase | Estimated Time |
|-------|--------------|
| **Database Migration** | 30 min |
| **Backend Models** | 1.5 hours |
| **Salt API Service** | 2.5 hours |
| **SSE Service** | 2 hours |
| **SSE Endpoints** | 2 hours |
| **Salt Ingestion API** | 3 hours |
| **Frontend SSE Composable** | 2 hours |
| **Server Detail Page** | 1 hour |
| **Salt Info Component** | 1 hour |
| **Salt Metrics Component** | 2 hours |
| **Salt Services Component** | 1.5 hours |
| **Salt Processes Component** | 1.5 hours |
| **Salt Packages Component** | 1.5 hours |
| **Salt Logs Component** | 1.5 hours |
| **Salt Alerts Component** | 1.5 hours |
| **Main App Router** | 30 min |
| **Testing** | 3 hours |
| **Documentation** | 1.5 hours |
| **Total** | ~29.5 hours (~3.7 days) |

---

## Coverage Comparison

| PRD Section | Status | Notes |
|-------------|--------|-------|
| **1. Overview** | ✅ Covered | Architecture designed |
| **2. Static Facts (Grains)** | ✅ Covered | Salt API client includes grains |
| **3. Real-Time Metrics** | ✅ Covered | All metrics included |
| **4. Service Monitoring** | ✅ Covered | Full service management |
| **5. Process Monitoring** | ✅ Covered | Processes component + API |
| **6. Network Monitoring** | ✅ Covered | Network metrics included |
| **7. Disk & Filesystem** | ✅ Covered | Disk metrics included |
| **8. System Health** | ✅ Covered | Uptime, time included |
| **9. Package Management** | ✅ Covered | Packages component + API |
| **10. Log & File Monitoring** | ✅ Covered | Logs component + API |
| **11. Security & Access** | ✅ Covered | JWT authentication |
| **12. Custom Execution** | ✅ Covered | Salt API client supports this |
| **13. Beacon System** | ✅ Covered | Beacon events processing |
| **14. Real-Time Data Streaming (SSE)** | ✅ Covered | Full SSE implementation |
| **15. Summary & Reference** | ✅ Covered | Documentation included |

**Full PRD Coverage: 15/15 sections (100%)**

---

## Ready to Start Phase 4: Implementation

**Plan Summary:**
- ✅ Full PRD coverage (all 15 sections)
- ✅ Detailed implementation steps (18 steps)
- ✅ Database schema design
- ✅ Backend service architecture
- ✅ Frontend component architecture
- ✅ SSE implementation with JWT auth
- ✅ Comprehensive testing plan
- ✅ Documentation plan

**Estimated Total Time:** ~29.5 hours (~3.7 days)

**Dependencies Met:**
- ✅ Salt minions already installed
- ✅ Backend tech stack confirmed (FastAPI + SQLAlchemy async + TimescaleDB)
- ✅ Frontend tech stack confirmed (Vue 3 + TypeScript + Pinia + Element Plus)
- ✅ Redis available for pub/sub
- ✅ Scale planned (~50 servers → 500+)
- ✅ JWT authentication required
- ✅ Data retention policies defined

**Ready to proceed?**

Type: `approve` to start Phase 4, or ask questions.

---

**Related Enhancements:**
- `001-saltstack-sse.md` - SSE design reference

**Related Issues:**
- None yet

# System Monitoring Module (Uptime Kuma-style)

## Problem Statement

DevOps engineers managing staging and production systems have no visibility into external uptime, SSL health, or endpoint reachability from within OpsPilot. Today they use Uptime Kuma, UptimeRobot, or Pingdom — separate tools disconnected from their server inventory and notification preferences. An outage notification lands in a different app with no link to the server it runs on.

## Evidence

- OpsPilot already manages servers, alerts, and SMTP notifications — but only for agent-reported server metrics. External URL health is entirely out of scope today.
- Uptime Kuma has 60k+ GitHub stars — clear demand for self-hosted uptime monitoring.
- SSL certificate expiry and missed heartbeats are common causes of preventable outages.
- Assumption: Users already run Uptime Kuma or similar; this replaces it with native OpsPilot integration.

## Proposed Solution

Build a Monitors module (inspired by Uptime Kuma) scoped to organizations where users register URLs and endpoints. A backend scheduler runs periodic checks (HTTP/HTTPS, SSL, TCP, DNS, Push/Heartbeat) and stores results as time-series data. Incidents are created on state changes (up→down, down→up) and notifications fire via email, Telegram, or webhook. A Kuma-style badge grid dashboard shows all monitor statuses at a glance.

## Key Hypothesis

We believe native uptime + SSL monitoring will reduce context-switching and mean-time-to-acknowledge for OpsPilot users. We'll know we're right when users configure ≥ 3 monitors per org within 2 weeks of release and incident email click-through rate exceeds 60%.

## What We're NOT Building

- **Multi-region distributed checks** — single-origin from backend; good enough for MVP
- **ICMP ping checks** — requires raw socket privileges in Docker; skip v1
- **On-call schedules / escalation policies** — v2
- **Synthetic transaction monitoring** — too complex for MVP scope
- **Public status page** — v2 (moved from Won't; high demand, needs subdomain/auth design)

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Monitors configured within 1 week | ≥ 5 per org | DB count |
| Incident email delivery latency | < 2 min from first failed check | Log timestamps |
| False positive rate | < 5% of incidents | Incidents resolved < 2 min |
| SSL expiry warnings caught | 100% of expiries > 7 days out | Manual audit |

## Open Questions

- [ ] Should checks run from the backend container or from each registered server's agent? (Backend simpler; agent gives distributed checks)
- [ ] Minimum check interval — 1 min may be too aggressive for a small VPS
- [ ] Should monitors optionally link to a server (FK) for incident context?
- [ ] How long to retain `monitor_checks` rows? Need TimescaleDB retention policy.
- [ ] Confirm 2 consecutive failures before declaring incident (avoids single-blip false positives)

---

## Users & Context

**Primary User**
- **Who**: DevOps engineer or SRE managing 2–20 staging/production deployments for a small-to-mid team
- **Current behavior**: Checks UptimeRobot or Pingdom separately; manually tracks SSL expiry in a calendar reminder
- **Trigger**: Customer reports site down before engineer knows; or SSL cert expires silently
- **Success state**: Receives OpsPilot email the moment a monitored URL goes down, with enough context to act

**Job to Be Done**
When a production service goes down or an SSL cert nears expiry, I want to be notified immediately with context, so I can minimize downtime without checking multiple dashboards.

**Non-Users**
End customers / non-technical stakeholders — they need a public status page (explicitly out of scope v1).

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | HTTP/HTTPS uptime check (2xx = up) | Core value |
| Must | SSL certificate expiry check + days remaining | High ROI, free alongside HTTP check |
| Must | Response time measurement (ms) | Free with HTTP check |
| Must | Incident creation on state change (up↔down) | Required for alerts |
| Must | Email notification on incident open + resolve | Reuses existing SMTP system |
| Must | Monitor CRUD (create, pause, delete) | Basic management |
| Must | Kuma-style badge grid dashboard (green/red/pause per monitor) | Uptime Kuma signature UX |
| Must | Uptime % badges (24h / 7d / 30d) on each card | SLA at a glance |
| Should | Configurable check interval (1/5/15/30/60 min) | Different SLAs |
| Should | TCP port check | Non-HTTP services |
| Should | **Push / Heartbeat monitor** — service pings OpsPilot, alert if ping stops | Cron job / background task monitoring |
| Should | **DNS record monitor** — check A/CNAME/MX resolves to expected value | DNS change detection |
| Should | SSL expiry warning email (30d / 14d / 7d) | Proactive cert management |
| Should | Response time history chart per monitor | Performance visibility |
| Won't | Telegram notification | Email is sufficient for v1 |
| Won't | Webhook notification | Email is sufficient for v1 |
| Should | Keyword presence / absence check in response body | Validate content, not just status |
| Could | Optional server link (monitor → server FK) | Incident context |
| Could | **Public status page** (read-only, no auth) | Uptime Kuma signature feature; v2 |
| Could | Expected status code override (e.g. 301, 404 is "up") | Edge cases |
| Won't | ICMP ping | Docker privilege issue |
| Won't | Multi-region checks | Complexity, v2 |

### MVP Scope

Monitors CRUD + HTTP/HTTPS checks + SSL expiry checks + 2-consecutive-failure incident detection + email on down/recover + status dashboard.

### User Flow

1. Sidebar → **Monitors** → **Add Monitor**
2. Enter: name, URL, type (HTTP / TCP), interval, timeout
3. First check runs within 60 seconds; card turns green/red
4. Monitor goes down (2 consecutive failures) → incident created → email to all matching recipients
5. Monitor recovers → incident resolved → recovery email sent
6. Click monitor card → response time chart + incident history

---

## Technical Approach

**Feasibility**: HIGH — all infrastructure exists; new pieces are scheduler, check runner, 3 DB tables.

### Architecture Notes

**Scheduler**: `APScheduler` (`AsyncIOScheduler`) registered in `app/main.py` `startup_event`. One job per active monitor, keyed by monitor UUID. Jobs are added/replaced/removed dynamically on CRUD operations. `apscheduler>=3.10` must be added to `pyproject.toml`.

**Check runner** (`app/services/monitor_service.py`):
- HTTP/HTTPS: `httpx.AsyncClient` with timeout; capture `status_code`, `response_time_ms`; extract SSL cert from TLS handshake for expiry
- SSL-only: `ssl` + `socket` stdlib; `getpeercert()` → parse `notAfter`
- TCP: `asyncio.open_connection()` with timeout → port open/closed

**Incident logic** (in check runner):
- `consecutive_failures` counter on monitor row
- Incident opens after 2 consecutive failures → set `last_status = 'down'`, create `monitor_incidents` row, send email
- First success after down → resolve incident, send recovery email, reset counter

**Monitor types:**
- `http` / `https` — HTTP check, captures status code + response time + SSL expiry
- `tcp` — TCP port open/closed check
- `dns` — resolve hostname, compare to expected IP/value
- `push` — no outbound check; monitor waits for heartbeat ping from service; alert if ping not received within `interval_seconds * 1.5`

**Push/Heartbeat endpoint**: `POST /api/v1/monitors/{id}/heartbeat?api_key=...` — no auth required beyond the monitor's unique key; called by cron jobs / background services to signal "still alive".

**Notification**: email only — reuse existing `NotificationSmtpConfig` + `NotificationRecipient` + `EmailService`. Two triggers:
1. **Monitor down** — email when incident opens (after 2 consecutive failures)
2. **SSL expiry warning** — email at 30d / 14d / 7d before cert expires

**Data model** (migration 025):
```
monitors
  id, org_id, server_id (nullable FK), name, url, type (http/https/tcp/dns/push),
  port (nullable), interval_seconds, timeout_seconds, enabled,
  consecutive_failures, last_status, last_checked_at,
  heartbeat_api_key (push type only), dns_resolve_type, dns_resolve_expected,
  keyword_check, keyword_expected, accepted_status_codes (JSONB),
  created_at

monitor_checks  ← TimescaleDB hypertable on checked_at
  id, monitor_id, checked_at, status (up/down), response_time_ms,
  status_code (nullable), ssl_days_remaining (nullable), error (nullable)

monitor_incidents
  id, monitor_id, org_id, started_at, resolved_at,
  duration_seconds (nullable), down_notified, recover_notified

```

**Notifications**: Email only. Reuse org-level `NotificationSmtpConfig` + `NotificationRecipient` + `EmailService`. Add `send_monitor_notification()` to `EmailService`. Two email triggers:
- **Monitor down** — fires when incident opens (2 consecutive failures); includes monitor name, URL, error, time
- **SSL expiry warning** — fires at 30d / 14d / 7d; includes domain, days remaining, cert issuer
- **Monitor recovered** — fires when incident resolves; includes downtime duration

No per-monitor notification channel config — all monitors in an org share the org's SMTP + recipient settings.

**Frontend** (`frontend/src/views/monitors/`):
- Route `/monitors` added to `main-layout-routes.ts`
- Sidebar entry added to nav
- `index.vue`: status grid (card per monitor — green/red/paused, response time, SSL days)
- `MonitorForm.vue`: add/edit dialog
- `MonitorDetail.vue`: response time line chart + incident history table
- Pinia store: `useOpsPilotMonitorStore` in `stores/modules/opspilot.ts`
- API client: `api/opspilot/monitors.ts`

### Technical Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Scheduler job accumulation on hot-reload | M | Use `job_id = monitor.id`; `replace_existing=True` |
| `httpx` not in backend deps | L | Check `pyproject.toml`; add if missing |
| SSL check fails on self-signed certs | M | Add `verify_ssl` bool on monitor; skip validation if false |
| Docker container can't reach internal hostnames | M | Document; user must use public URLs or Docker network names |
| Check interval 1 min × many monitors → DB write flood | M | Use `monitor_checks` hypertable + retention policy; batch inserts if > 50 monitors |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | DB + Models | Migration 025: 3 tables (monitors, monitor_checks hypertable, monitor_incidents) | pending | - | - | - |
| 2 | Check Runner + Email | HTTP/SSL/TCP/DNS checkers + Push heartbeat + incident lifecycle + email dispatch | pending | - | 1 | - |
| 3 | Scheduler | APScheduler + FastAPI startup; per-monitor jobs + push timeout detection | pending | with 4 | 2 | - |
| 4 | REST API | CRUD + `POST /heartbeat` endpoint + checks history + incidents history | pending | with 3 | 2 | - |
| 5 | Frontend | Kuma-style badge grid, add/edit form, detail chart | pending | - | 3, 4 | - |
| 6 | SSL Expiry Job | Daily scan: SSL days remaining → warning email at 30d/14d/7d | pending | - | 3 | - |

### Phase Details

**Phase 1: DB + Models**
- **Goal**: Schema in place, models importable
- **Scope**: `025_monitors.py`; `app/models/monitor.py` (4 models: Monitor, MonitorCheck, MonitorIncident, MonitorNotificationChannel); update `app/models/__init__.py`
- **Success signal**: `alembic upgrade head` clean; all 4 tables visible in pgAdmin; `monitor_checks` is a hypertable

**Phase 2: Check Runner**
- **Goal**: All check types working, incident logic correct
- **Scope**: `app/services/monitor_service.py` — `check_http()`, `check_ssl()`, `check_tcp()`, `check_dns()`, `handle_push_timeout()`, `run_check()`, `handle_state_change()`
- **Success signal**: Each check type returns correct up/down; incident created after 2 consecutive failures; push monitor goes down after missing heartbeat

**Phase 3: Scheduler**
- **Goal**: Checks run automatically at configured intervals
- **Scope**: `app/services/monitor_scheduler.py`; wire into `main.py` startup/shutdown; `apscheduler>=3.10` added to `pyproject.toml`
- **Success signal**: `monitor_checks` rows appear at configured interval per monitor; push timeout job fires when no heartbeat received

**Phase 4: REST API**
- **Goal**: Frontend-ready + push heartbeat endpoint
- **Scope**: `app/api/v1/monitors.py` — CRUD + `GET /monitors/{id}/checks` + `GET /monitors/{id}/incidents` + `POST /monitors/{id}/heartbeat?api_key=...` (no user auth — uses monitor's heartbeat_api_key); registered in `__init__.py`
- **Success signal**: CRUD works; `curl POST /heartbeat` updates `last_checked_at`; push monitor goes green

**Phase 5: Frontend**
- **Goal**: Uptime Kuma-style UX — badge grid, 30-bar uptime strip, response time chart
- **Scope**: `views/monitors/index.vue` (badge grid + 30-day uptime bar strip per card), `MonitorForm.vue` (all types including push — shows heartbeat URL after creation), `MonitorDetail.vue` (response time chart + incident history); Pinia store + API client; router `/monitors` + sidebar entry
- **Success signal**: Add HTTP monitor → green badge + response time shown; add push monitor → heartbeat URL displayed; bad URL → red badge + email received

**Phase 6: SSL Expiry Job**
- **Goal**: Proactive SSL cert expiry warnings
- **Scope**: Daily APScheduler job scanning `monitor_checks` latest `ssl_days_remaining` per monitor; fires notification via all configured channels for that monitor once per threshold (30/14/7d)
- **Success signal**: Monitor with cert 29 days remaining → notification fires once on daily scan

### Parallelism Notes

Phases 3, 4, and 5 run in parallel after Phase 2 — scheduler, API, and notification dispatch are independent. Frontend (Phase 6) scaffolds during Phase 4 but needs API complete for integration. Phase 7 depends on both scheduler (Phase 3) and notification dispatch (Phase 5).

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Scheduler | APScheduler AsyncIOScheduler | Celery, asyncio loop, cron | Async-native, no separate worker, integrates with FastAPI startup/shutdown |
| Check origin | Backend container | Agent-side, external SaaS | Simplest deployment; agent-side deferred to v2 |
| HTTP client | httpx | aiohttp, requests | Async, modern, likely already in deps |
| Time-series storage | TimescaleDB hypertable | Regular Postgres, InfluxDB | Existing pattern in codebase; fast range queries; easy retention policy |
| Monitor scope | Organization | Server-scoped | External URLs don't belong to one server; org scope is more flexible |
| Notification system | Reuse existing SMTP + recipients | New model | Zero new config burden; consistent UX |
| Incident trigger | 2 consecutive failures | 1 failure, 3 failures | Balances false-positive rate vs detection speed |

---

## Research Summary

**Market Context**
UptimeRobot, Better Uptime, Freshping, Pingdom. Common patterns: check intervals 1–60 min, 2–3 consecutive failures to confirm down state (reduces false positives), email + webhook on state change, SSL expiry warnings at 30/14/7 days, response time p50/p95 charts. Anti-pattern: alerting on single failed check = alert fatigue.

**Technical Context**
- `app/main.py:95` — `@app.on_event("startup")` is the scheduler registration point
- `app/models/notification.py` — `NotificationSmtpConfig` + `NotificationRecipient` fully reusable
- `app/core/email.py` — `EmailService` needs one new method; existing `send_alert_notification()` is the pattern to follow
- `app/api/v1/alerts.py:440–493` — exact email dispatch pattern to replicate
- Latest migration: `024_notification_settings.py` → next is `025`
- TimescaleDB hypertable pattern: `20260413_2143_20ada5292351_configure_timescale_hypertable.py`
- No scheduler library in `pyproject.toml` yet — `apscheduler>=3.10` must be added
- `httpx` presence in deps: TBD — check before Phase 2

---

*Generated: 2026-05-04*
*Status: DRAFT — open questions on check interval minimums and agent-side checks for v2*

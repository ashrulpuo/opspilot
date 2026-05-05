# Salt Minion SSH Auto-Install (Add Server)

**ID:** 003  
**Category:** infrastructure  
**Date:** 2026-04-21  
**Status:** ✅ Implemented  
**Related:** [002-saltstack-implementation.md](./002-saltstack-implementation.md), [002-saltstack-ux.md](./002-saltstack-ux.md)

## Purpose

When an operator adds a Linux server with **“Auto-install Salt minion”** enabled, OpsPilot SSHs to the target, installs `salt-minion` if missing (official [bootstrap.saltproject.io](https://bootstrap.saltproject.io)), writes minion configuration, and restarts the service.

This complements the **HTTP push** ingestion described in `002-saltstack-implementation.md`: minions can still report to the FastAPI `/api/v1/salt/...` endpoints; having a real **Salt master** is optional but supported for classic Salt workflows (grains, states, key acceptance on the master).

## Clarification vs 002 Planning Doc

| Topic | 002 (original plan) | Current behavior (003) |
|--------|---------------------|-------------------------|
| Salt master | “No master” in architecture diagram | **Optional.** If you use SSH auto-install, set **`SALT_MASTER_HOST`** on the API so new minions know where to connect. |
| Minion on server | “Already installed — skip auto-install” | **Optional.** UI + API can **auto-install** minion over SSH when credentials are provided. |
| Data path to OpsPilot | Minions push to backend API | Unchanged: `/api/v1/salt/*` + metrics paths remain the ingestion surface once runners/beacons are configured. |

## Configuration (API / Compose)

| Variable | Required for SSH auto-install | Description |
|----------|--------------------------------|-------------|
| `SALT_MASTER_HOST` | **Yes** | Hostname or IP of the Salt master **as seen from the target server** (written to `/etc/salt/minion.d/99-opspilot.conf`). |

Also set **`SALT_API_KEY`** for Salt runners calling the API (unchanged from 002).

Documented in `deploy/.env.example`. Production compose passes `SALT_MASTER_HOST` into the backend service (`docker-compose.prod.yml`).

## Minion identity (must match pillar)

- **Minion `id`:** `opspilot-minion-{server_uuid}`  
  Same string used in `ServerService._setup_salt_minion()` for Salt pillar keys (`server_service.py`).

After install, on the **Salt master**, accept the key if required:

```bash
sudo salt-key -L
sudo salt-key -a 'opspilot-minion-<server_uuid>'
```

## Code references

| Area | Path |
|------|------|
| SSH install (bootstrap + minion.d + systemd) | `backend/app/services/agent_ssh_install.py` |
| Background task after `POST .../servers` | `backend/app/services/background_agent_install.py` |
| API validation (`SALT_MASTER_HOST` when auto-install) | `backend/app/api/v1/servers.py` |
| Pillar / minion naming | `backend/app/services/server_service.py` (`_setup_salt_minion`) |
| Settings | `backend/app/core/config.py` → `SALT_MASTER_HOST` |
| UI copy | `frontend/src/views/servers/index.vue` |

## Target server requirements

- **Linux** (same constraint as API validator).
- **SSH** username + password (stored encrypted for future OpsPilot SSH features).
- **`sudo` without password** for non-root users, or **root** over SSH (installer runs `systemctl` and writes under `/etc/salt`).
- **Outbound access** to `bootstrap.saltproject.io` for first-time install (curl or wget on target).
- **DNS/network** from target to `SALT_MASTER_HOST` (ports 4505/4506 to master as per your Salt topology).

## Testing

1. Set `SALT_MASTER_HOST` on the API container/host.
2. Add server with auto-install + valid SSH.
3. On master: verify minion key and `salt 'opspilot-minion-*' test.ping`.
4. Confirm OpsPilot receives heartbeats/metrics on `/api/v1/salt/...` when your Salt side is wired to POST there.

## Deployment checklist

- [ ] `SALT_MASTER_HOST` set in `deploy/.env` (or compose `environment`).
- [ ] Master firewall allows minions (4505/4506).
- [ ] Master accepts new minion keys (auto-accept or manual `salt-key`).
- [ ] Pillar/API URLs in Salt states match `PUBLIC_API_BASE_URL` where runners call OpsPilot.

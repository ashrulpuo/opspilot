# Infrastructure Registry Module

## Problem Statement

DevOps engineers managing multiple staging and production environments have no single place in OpsPilot to catalog infrastructure assets — domain names, SSL certificates, database services, and login credentials. These are scattered across password managers, spreadsheets, and team wikis with no link to the servers and organizations already managed in OpsPilot. Onboarding a new team member or responding to an incident requires hunting across multiple tools.

## Evidence

- OpsPilot has org → server hierarchy but no asset catalog layer.
- Existing `credentials.py` API is server-scoped SSH/API keys only via HashiCorp Vault — Vault is currently unhealthy and unused.
- Domain expiry and DB credential loss are common causes of preventable outages.
- Assumption: Teams use 1Password / Bitwarden / Notion for this today — needs validation.

## Proposed Solution

Build an Infrastructure Registry module scoped to organizations. Users catalog: domains (with expiry), SSL certificates (with expiry), database services (MySQL/Postgres/Redis/etc. with encrypted credentials), and general credentials (web logins, API keys, tokens). All sensitive fields encrypted at rest using `Fernet` (AES-128-CBC — already available via `cryptography` package in existing deps). Secrets never returned in list/get responses — only via explicit `/reveal` endpoint that writes an audit log entry.

## Key Hypothesis

We believe a centralized encrypted infrastructure registry inside OpsPilot will reduce time-to-context during incidents and eliminate credential-hunting across external tools. We'll know we're right when users add ≥ 5 assets within 1 week and reference the registry during at least one incident response.

## What We're NOT Building

- **Auto-rotation of credentials** — v2; requires per-service integration
- **HashiCorp Vault backend** — Vault is unhealthy; use app-level Fernet for v1
- **SSH key storage** — already exists in `credentials.py`; don't duplicate
- **Fine-grained per-asset ACL** — all org members see all assets; v2
- **Import from 1Password / Bitwarden** — v2
- **Auto SSL provisioning (Let's Encrypt)** — out of scope; catalog only

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Assets added per org within 1 week | ≥ 5 | DB count |
| Zero plaintext credentials in DB | 100% | Automated audit query |
| Audit log entries (reveals) within 2 weeks | > 0 | DB count |
| Asset list page load | < 500ms p95 | Browser perf |

## Open Questions

- [ ] Should DB service assets test connection (ping host:port) on save?
- [ ] Reveal: show inline or require re-auth confirmation first?
- [ ] Should domain/SSL expiry warnings reuse monitor notification system or standalone daily job?
- [ ] Fernet key rotation strategy if `ASSET_ENCRYPTION_KEY` is compromised?
- [ ] Link SSL certs in registry to SSL monitors from system-monitoring PRD — same entity or separate?

---

## Users & Context

**Primary User**
- **Who**: DevOps engineer or tech lead managing 3–30 infrastructure assets across staging/production for a small team
- **Current behavior**: Stores DB passwords in shared Notion / 1Password; looks up domain expiry in registrar dashboard manually
- **Trigger**: New team member joins and needs all credentials; or an incident reveals the team can't find the staging DB password
- **Success state**: Opens OpsPilot → Registry → finds staging Postgres credentials in under 10 seconds

**Job to Be Done**
When I need credentials or need to check when a domain expires, I want a single encrypted registry inside my ops tool, so I can stop context-switching to a separate password manager.

**Non-Users**
End customers — no access to OpsPilot at all.

---

## Solution Detail

### Asset Types

**Domains**: name, registrar, registered_at, expires_at, auto_renew, nameservers, notes, tags, linked_server_id (nullable)

**SSL Certificates**: domain_name, common_name, issuer, issued_at, expires_at, fingerprint, auto_renew, provider (Let's Encrypt/manual/Cloudflare/etc.), notes, linked_domain_id (nullable)

**Database Services**: name, db_type (mysql/postgres/redis/mongodb/mariadb/other), host, port, database_name, username, **password_enc** (Fernet), environment (dev/staging/prod), ssl_enabled, notes, tags, linked_server_id (nullable)

**Credentials (General)**: name, credential_type (web_login/api_key/token/smtp/ftp/other), url, username, **secret_enc** (Fernet), environment, notes, tags, linked_server_id (nullable)

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Domain CRUD with expiry date | Core catalog |
| Must | SSL Certificate CRUD with expiry date | Core catalog |
| Must | Database Service CRUD with encrypted credentials | Replaces spreadsheet |
| Must | General Credential CRUD with encrypted secret | Core value |
| Must | Fernet encryption for all password/secret fields | Security requirement |
| Must | Audit log: who revealed which credential, when | Accountability |
| Must | Copy-to-clipboard without revealing in UI | Security UX |
| Must | Masked display with show/hide toggle (auto-re-mask 30s) | Security UX |
| Should | Environment filter (dev/staging/prod) | Multi-env management |
| Should | Domain expiry email warning (30d/14d/7d) | Proactive expiry |
| Should | SSL cert expiry email warning (30d/14d/7d) | Proactive expiry |
| Should | Search across all asset types | Usability |
| Should | Tags for grouping | Organization |
| Should | Optional link to server | Incident context |
| Could | DB connection test (ping host:port on save) | Validation UX |
| Could | Bulk CSV import | Onboarding |
| Won't | Credential auto-rotation | v2 |
| Won't | Vault backend | v2 |
| Won't | Per-asset ACL | v2 |

### MVP Scope

All 4 asset types CRUD + Fernet encryption + masked display + copy-to-clipboard + audit log + environment filter + search.

### User Flow

1. Sidebar → **Registry** → tabs: Domains | SSL | Databases | Credentials
2. **Add** button → type-specific form dialog
3. Passwords show as `••••••••` with eye icon + copy icon
4. Eye → reveals inline, auto-re-masks after 30 seconds → audit log written
5. Copy → clipboard without revealing in UI → audit log written
6. Filter by environment, search by name/host
7. Click asset → detail with full fields + audit log entries for this asset

---

## Technical Approach

**Feasibility**: HIGH — encryption library in existing deps; follows established org-scoped patterns.

### Encryption Strategy

`cryptography.fernet.Fernet` — symmetric AES-128-CBC + HMAC-SHA256:

```python
# app/core/asset_encryption.py
from cryptography.fernet import Fernet
from app.core.config import settings

_fernet = Fernet(settings.ASSET_ENCRYPTION_KEY.encode())

def encrypt_secret(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()

def decrypt_secret(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()
```

`ASSET_ENCRYPTION_KEY` = 44-char URL-safe base64 Fernet key in `.env`. **Never in DB.**

List/Get responses omit password fields entirely. Only `GET /reveal` returns decrypted value + writes audit entry.

### Data Model (migration 025 or 026)

```
registry_domains
  id, org_id, server_id (nullable FK), name, registrar,
  registered_at, expires_at, auto_renew, nameservers,
  notes, tags (JSONB), created_at, updated_at

registry_ssl_certs
  id, org_id, domain_id (nullable FK), domain_name, common_name,
  issuer, issued_at, expires_at, fingerprint, auto_renew,
  provider, notes, created_at, updated_at

registry_db_services
  id, org_id, server_id (nullable FK), name, db_type, host, port,
  database_name, username, password_enc (TEXT), environment,
  ssl_enabled, notes, tags (JSONB), created_at, updated_at

registry_credentials
  id, org_id, server_id (nullable FK), name, credential_type,
  url, username, secret_enc (TEXT), environment,
  notes, tags (JSONB), created_at, updated_at

registry_audit_log
  id, org_id, user_id (FK), asset_type, asset_id,
  action (reveal/create/update/delete), ip_address, created_at
```

### API Surface

```
POST/GET/PUT/DELETE  /api/v1/registry/domains/{id?}
GET                  /api/v1/registry/domains/{id}/reveal   ← N/A (no secrets)

POST/GET/PUT/DELETE  /api/v1/registry/ssl-certs/{id?}

POST/GET/PUT/DELETE  /api/v1/registry/databases/{id?}       ← password_enc omitted
GET                  /api/v1/registry/databases/{id}/reveal ← decrypts + audit log

POST/GET/PUT/DELETE  /api/v1/registry/credentials/{id?}     ← secret_enc omitted
GET                  /api/v1/registry/credentials/{id}/reveal ← decrypts + audit log

GET                  /api/v1/registry/audit-log             ← org-scoped
GET                  /api/v1/registry/search?q=             ← cross-type, no secrets
```

### Frontend Structure

```
frontend/src/views/registry/
  index.vue                ← tabbed: Domains | SSL | Databases | Credentials
  components/
    DomainList.vue + DomainForm.vue
    SslCertList.vue + SslCertForm.vue
    DatabaseList.vue + DatabaseForm.vue
    CredentialList.vue + CredentialForm.vue
    SecretField.vue          ← reusable: masked input, reveal-30s, copy
    AssetAuditLog.vue
```

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `ASSET_ENCRYPTION_KEY` lost = secrets unrecoverable | H | Document backup; store in env manager; add to deploy checklist |
| `cryptography` only transitive dep (via python-jose) | M | Add explicit `cryptography>=42.0` to `pyproject.toml` |
| Key rotation after compromise | M | Add `/admin/registry/re-encrypt` endpoint in v1.5; document manual rotation |
| Fernet ciphertext larger than plaintext | L | TEXT column is unbounded |
| User enters wrong DB password — undetectable until use | L | Optional connection test button on DB form |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | Encryption Utility | `asset_encryption.py`, `ASSET_ENCRYPTION_KEY` config, `cryptography` dep | pending | - | - | - |
| 2 | DB + Models | Migration: 5 tables + SQLAlchemy models | pending | with 1 | - | - |
| 3 | REST API | `registry.py` router: all 4 types + reveal + audit log + search | pending | - | 1, 2 | - |
| 4 | Expiry Warnings | Daily job: domain + SSL cert expiry → email at 30/14/7d | pending | with 3 | 1, 2 | - |
| 5 | Frontend | Tabbed views, SecretField component, Pinia store, API client | pending | - | 3 | - |

### Phase Details

**Phase 1: Encryption Utility**
- **Goal**: Encryption roundtrip working in container
- **Scope**: `app/core/asset_encryption.py`; add `ASSET_ENCRYPTION_KEY` to `config.py` + `.env.example`; add `cryptography>=42.0` to `pyproject.toml`; document key generation (`Fernet.generate_key()`)
- **Success signal**: `encrypt_secret("test") → decrypt_secret(...)` returns `"test"` in backend container

**Phase 2: DB + Models**
- **Goal**: Tables in DB, models importable
- **Scope**: `025_registry.py` (or 026); `app/models/registry.py` (5 models); update `app/models/__init__.py`
- **Success signal**: `alembic upgrade head` clean; all 5 tables in pgAdmin

**Phase 3: REST API**
- **Goal**: Complete CRUD + secure reveal + audit + search
- **Scope**: `app/api/v1/registry.py`; registered in `app/api/v1/__init__.py`; passwords encrypted on write, omitted on list/get, decrypted only on `/reveal` with audit entry written
- **Success signal**: POST db service → GET list omits password → GET /reveal returns password → audit log has entry

**Phase 4: Expiry Warnings**
- **Goal**: Email warnings before domain/cert expiry
- **Scope**: APScheduler daily job scanning `registry_domains.expires_at` and `registry_ssl_certs.expires_at`; sends via existing `EmailService`; fires once per threshold (30/14/7d)
- **Success signal**: Record with `expires_at = now+29d` → email fires on next daily scan

**Phase 5: Frontend**
- **Goal**: Full asset management UX with secure credential handling
- **Scope**: All Vue components + `SecretField.vue` (mask/reveal-30s/copy) + Pinia store + API client + router `/registry` + sidebar entry
- **Success signal**: Add DB → masked password shown → eye reveals 30s → copy works → audit log populated

### Parallelism Notes

Phases 1 and 2 can run in parallel (encryption utility and DB schema are independent). Phase 4 (expiry warnings) can start in parallel with Phase 3 (API) since it only needs models. Frontend (Phase 5) depends on the API being complete.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Encryption | Fernet app-level | HashiCorp Vault, pgcrypto | Vault unhealthy; pgcrypto adds DB coupling; Fernet is simple + already in deps |
| Secret reveal model | Explicit `/reveal` + audit log | Return in GET | Prevents exposure in logs/traces; enables accountability |
| Asset scope | Organization | Server-scoped | DB services and domains aren't tied to one server |
| Migration number | 025 or 026 | - | Depends on whether system-monitoring PRD is built first |
| Frontend layout | Single `/registry` with tabs | Separate routes per type | Reduces nav clutter; all asset types are related |

---

## Research Summary

**Market Context**
1Password Teams, Bitwarden, Doppler, Infisical, HashiCorp Vault. Key UX patterns: secrets never in list responses, explicit reveal action, audit log non-negotiable, encryption key outside DB, copy-without-reveal standard. Infisical and Doppler are closest analogues (developer-focused secrets + infrastructure metadata).

**Technical Context**
- `app/core/vault.py` — Vault client exists but container is `unhealthy`; not reliable for v1
- `app/api/v1/credentials.py` — existing server-scoped SSH credential API; different scope, don't conflict
- `pyproject.toml:22` — `python-jose[cryptography]` brings `cryptography` package; `Fernet` available
- `app/core/config.py` — Pydantic settings pattern; `ASSET_ENCRYPTION_KEY` fits cleanly
- Latest migration: `024_notification_settings.py` → next: `025` (or `026` if monitoring PRD built first)
- Org-scoped FK pattern: established in `app/models/organization.py` and all existing org-scoped models
- Auth pattern for org membership check: `app/api/v1/alerts.py:89–115` — replicate exactly

---

*Generated: 2026-05-04*
*Status: DRAFT — open questions on key rotation strategy and DB connection test*

# Enhancements Documentation

This folder contains all enhancement documentation for OpsPilot.

## Purpose

All enhancements, features, and improvements made to the OpsPilot system are documented here in separate markdown files.

## Structure

```
enhancements/
├── README.md                           # This file
├── 001-saltstack-sse.md                # SSE implementation for real-time metrics
├── 002-saltstack-implementation.md     # Salt data collection plan (API push architecture)
├── 002-saltstack-implementation-full.md
├── 002-saltstack-ux.md                 # Server detail / Salt UI design
├── 003-salt-minion-ssh-auto-install.md # SSH Salt minion install when adding a server
└── ...
```

## Naming Convention

- Format: `{nnn}-{brief-description}.md`
- `{nnn}`: Sequential number (001, 002, 003, ...)
- `{brief-description}`: Short, lowercase, hyphen-separated description

## Categories

- **sse** - Real-time data streaming
- **monitoring** - Metrics, alerts, health checks
- **ui** - Frontend enhancements
- **api** - Backend API enhancements
- **database** - Database optimizations
- **infrastructure** - Docker, deployment, CI/CD
- **security** - Security improvements
- **performance** - Performance optimizations

## How to Add New Enhancement

1. Create new file: `{nnn}-{category}-{name}.md`
2. Document:
   - **Purpose** - What problem does this solve?
   - **Changes** - What files/code were changed?
   - **Impact** - How does this affect the system?
   - **Testing** - How was this tested?
   - **Deployment** - Any special deployment steps?
3. Update this README with the enhancement
4. Commit with message: `feat: add {brief-description}`

## Enhancement Log

| # | Document | Category | Status |
|---|----------|----------|--------|
| 001 | [001-saltstack-sse.md](./001-saltstack-sse.md) | sse | ✅ Implemented |
| 002 | [002-saltstack-implementation.md](./002-saltstack-implementation.md) | infrastructure | 📋 Planning / partial (see 003 for SSH minion) |
| 002 | [002-saltstack-implementation-full.md](./002-saltstack-implementation-full.md) | infrastructure | 📋 Ready to implement |
| 002 | [002-saltstack-ux.md](./002-saltstack-ux.md) | design | 📋 Design complete |
| 003 | [003-salt-minion-ssh-auto-install.md](./003-salt-minion-ssh-auto-install.md) | infrastructure | ✅ Implemented |

**Salt stack:** Start with **002** (architecture + API), **001** (SSE), **003** (SSH minion install at add-server). **002-saltstack-ux** is the UI spec for server detail.

---

**Last Updated:** 2026-04-21

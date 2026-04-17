# SaltStack UI/UX Design - Professional Dashboard

**ID:** 002-UX
**Category:** design
**Date:** 2026-04-17
**Status:** 📋 Design Complete
**Related:** 002-saltstack-implementation-full.md

## Overview

This document defines the professional, attractive UI/UX for displaying all SaltStack collected data in the OpsPilot frontend.

**Design Principles:**
- ✅ **Professional & Clean** - Enterprise-grade aesthetics
- ✅ **Information Hierarchy** - Visual importance through layout
- ✅ **Real-Time Updates** - Live data via SSE
- ✅ **Actionable Insights** - Clear controls for all data
- ✅ **Scanability** - At-a-glance status indicators
- ✅ **Modern & Responsive** - Mobile-friendly design
- ✅ **Data-Driven** - Charts, gauges, sparklines for metrics

---

## Overall Layout Strategy

### Server Detail Page Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Server Detail Header                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Server Name          Status ● Online    Last Seen 5m    │   │
│  │ IP: 192.168.1.100      Type: Physical      Uptime: 45d 2h    │   │
│  │ OS: Ubuntu 22.04       Region: US-East     CPU: 8 cores    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       Tabs Navigation                           │
│  [Overview] [Metrics] [Services] [Processes] [Packages] [Logs] [Alerts] │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                                                                 │
│                      Tab Content Area                          │
│  (Dynamic based on selected tab)                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       Action Bar                              │
│  [Restart Service] [Run Command] [Refresh] [SSH Terminal]   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Color Scheme

### Status Colors

| Status | Background | Text | Icon | Purpose |
|--------|-----------|------|------|---------|
| **Online** | `#10B981` | `#FFFFFF` | ○ | Healthy, running normally |
| **Warning** | `#F59E0B` | `#FFFFFF` | ⚠️ | Degraded, needs attention |
| **Error** | `#F56C6C` | `#FFFFFF` | ✕ | Error, failed |
| **Offline** | `#909399` | `#FFFFFF` | ○ | Disconnected, offline |
| **Unknown** | `#D9D9D9` | `#FFFFFF` | ○ | Status unknown |

### Metric Colors

| Metric Range | Color | Purpose |
|-------------|-------|---------|
| **0-50%** | `#67C23A` | ✅ Healthy, green zone |
| **50-70%** | `#E6A23C` | ⚠️ Warning, yellow zone |
| **70-85%** | `#F59E0B` | 🚨 High, orange zone |
| **85-100%** | `#F56C6C` | ❌ Critical, red zone |

### Alert Severity Colors

| Severity | Background | Text | Border |
|----------|-----------|------|--------|
| **Info** | `#E3F2FD` | `#FFFFFF` | `#E3F2FD` | Blue, informational |
| **Warning** | `#FFB800` | `#FFFFFF` | `#FFB800` | Amber, warning |
| **Critical** | `#DC2626` | `#FFFFFF` | `#DC2626` | Red, urgent |

### UI Colors (Element Plus Theme)

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| **Background** | `#F5F7FA` | `#1A1A1A` |
| **Card Background** | `#FFFFFF` | `#2C2C2C` |
| **Text Primary** | `#303133` | `#E5E5E5` |
| **Text Secondary** | `#606266` | `#909399` |
| **Border** | `#DCDFE6` | `#4C4C4C` |
| **Hover** | `#F5F7FA` | `#2C2C2C` |

---

## Typography

### Font Hierarchy

```
H1 (Page Title)     → 28px, Bold, "Inter", #303133
H2 (Section Header)  → 24px, Bold, "Inter", #303133
H3 (Card Title)      → 18px, Semibold, "Inter", #303133
H4 (Label)          → 14px, Medium, "Inter", #606266
Body Text          → 14px, Regular, "Inter", #606266
Small/Mono         → 12px, Regular, "JetBrains Mono", #909399
```

### Font Family

- **Primary:** Inter (Google Fonts) - Clean, professional, excellent readability
- **Secondary:** JetBrains Mono - For code, logs, metrics
- **Fallback:** system-ui, -apple-system, BlinkMacSystemFont

### Font Weights

- **Regular:** 400 - Body text, data labels
- **Medium:** 500 - Subheadings, card titles
- **Semibold:** 600 - Emphasis, important data
- **Bold:** 700 - Headers, call-to-action

---

## Component Designs

### 1. Server Detail Header

**Purpose:** At-a-glance server status, last seen, uptime

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Server Name: web01.prod.example.com               │   │
│  │                                           ● Online │   │
│  │                                           Last Seen: │   │
│  │                                           5m ago    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  IP Address: 192.168.1.100    Type: Physical    Uptime: 45d 2h  │
│  OS: Ubuntu 22.04.3 LTS     Region: US-East    Load: 2.3/2.1/1.8  │
│  CPU: Intel Xeon E5-2670     RAM: 32GB        Minion: Running    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Actions:                                    │   │
│  │ [Refresh Grains] [SSH] [Reboot]          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Real-Time Indicators:**
- **Status Badge:** Animated pulse effect when online
- **Last Seen:** Relative time (5m ago) with color degradation (gray → yellow → red)
- **Uptime:** Human-readable (45d 2h) with tooltip (3889720 seconds)

---

### 2. Overview Tab

**Purpose:** Static system info from grains, minion status

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ System Information                                   │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ OS Family:  Ubuntu          Architecture: x86_64  │  │   │
│  │ │ OS Release: 22.04.3 LTS     Kernel: 6.2.0-36-generic │  │   │
│  │ │ Hostname: web01           FQDN: web01.prod.example.com │  │   │
│  │ │ Domain: prod.example.com     IP: 192.168.1.100  │  │   │
│  │ └───────────────────────────────────────────────────────┘  │   │
│  │                                                        │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ Hardware Information                              │  │   │
│  │ ┌──────────────────────────────────────────────────────┐  │   │
│  │ │ CPU Model: Intel Xeon E5-2670 v4 @ 2.3GHz     │  │   │
│  │ │ CPU Cores: 16 (32 threads)                     │  │   │
│  │ │ RAM: 32 GB                                     │  │   │
│  │ │ Manufacturer: Dell Inc.                         │  │   │
│  │ │ Product: PowerEdge R740                        │  │   │
│  │ │ Serial: 7XH2K2                                 │  │   │
│  │ │ Type: Physical (Not VM)                         │  │   │
│  │ └───────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Storage Information                                 │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ Disk sda (Samsung SSD 970 EVO 1TB)        │  │   │
│  │ │ ┌─ Usage: 234GB / 1TB (23%)               │   │
│  │ │ └─ Type: SSD                                    │  │   │
│  │ │                                                  │  │   │
│  │ │ Disk sdb (Seagate ST4000 4TB HDD)            │  │   │
│  │ │ ┌─ Usage: 1.2TB / 4TB (30%)               │  │   │
│  │ │ └─ Type: HDD (rotational)                      │  │   │
│  │ │                                                  │  │   │
│  │ │ Filesystems:                                  │  │   │
│  │ │ / (sda)      ext4      234GB / 1TB (23%)    │  │   │
│  │ │ /var (sdb)    ext4      850GB / 4TB (21%)    │  │   │
│  │ │ /home (sdb)   ext4      400GB / 4TB (10%)    │  │   │
│  │ └───────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Network Information                                │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ Interface: eth0        MAC: 00:1a:2b:3c:4d:5e  │  │   │
│  │ │ ┌─ IPv4: 192.168.1.100    Netmask: 255.255.255.0 │  │   │
│  │ │ └─ IPv6: 2001:db8::1     Prefix: /64               │  │   │
│  │ │                                                  │  │   │
│  │ │ Gateway: 192.168.1.1     DNS: 8.8.8.8, 1.1.1.1  │  │   │
│  │ │                                                  │  │   │
│  │ │ Interface: eth1        MAC: 00:1a:2b:3c:4d:5f  │  │   │
│  │ │ ┌─ IPv4: 10.0.0.5        Netmask: 255.0.0.0     │  │   │
│  │ │ └─ IPv6: 2604::a8f       Prefix: /64               │  │   │
│  │ │                                                  │  │   │
│  │ │ Gateway: 10.0.0.1         DNS: 8.8.8.8, 1.1.1.1    │  │   │
│  │ └───────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Icon cards** for each section (System, Hardware, Storage, Network)
- **Progress bars** for disk usage with color coding
- **IP/MAC addresses** in monospace font for easy reading
- **Action buttons:** Refresh grains, SSH, Reboot

---

### 3. Metrics Tab (Real-Time)

**Purpose:** Live monitoring with charts, gauges, sparklines

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ CPU Usage (Real-Time)                            │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ Overall: 45.2%  ▓▓▓▓▓░░░░░░░░░░░░  │   │
│  │ │                                                  │   │   │
│  │ │ ┌───────────────────────────────────────────────────┐   │   │
│  │ │ │ CPU 0: 38.5%  ░░░░░░░░░░░░░░░  │   │   │
│  │ │ │ CPU 1: 42.3%  ▓▓▓▓▓▓░░░░░░░░░░  │   │   │
│  │ │ │ CPU 2: 51.2%  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░  │   │   │
│  │ │ │ CPU 3: 35.1%  ▓▓▓▓░░░░░░░░░░░░  │   │   │
│  │ │ │ CPU 4: 38.0%  ▓▓▓▓▓▓░░░░░░░░░░  │   │   │
│  │ │ │ ...                                         │   │   │
│  │ │ │ CPU 15: 41.8%  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  │   │   │
│  │ └───────────────────────────────────────────────────┘   │   │
│  │                                                  │   │   │
│  │ │ Time Range: [1h ▼]  Line Chart              │   │   │
│  │ │ ┌───────────────────────────────────────────────┐  │   │   │
│  │ │ │         📈                            │   │   │
│  │ │ │         45% ━━━━━━━━━━━━━━━━━━━━━━━ 30%   │   │   │
│  │ │ │         42% ━━━━━━━━━━━━━━━━━━━━━━━ 25%   │   │   │
│  │ │ │         35% ━━━━━━━━━━━━━━━━━━━━━ 20%   │   │   │
│  │ │ │         38% ━━━━━━━━━━━━━━━━━━━━━ 15%   │   │   │
│  │ │ │         41% ━━━━━━━━━━━━━━━━━━━━ 10%   │   │   │
│  │ │ │         38% ━━━━━━━━━━━━━━━━━━━━━ 5%    │   │   │
│  │ │ └───────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Memory Usage (Real-Time)                          │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ Total: 32 GB                                    │   │
│  │ │                                                  │   │   │
│  │ │ ┌─ Used: 28.8 GB (90%) ━━━━━━━━━━━━━━━━━━━  │   │   │
│  │ │   Available: 3.2 GB                          │   │   │
│  │ │   Swap: 4.2 GB / 32 GB (13%)                  │   │   │
│  │ └───────────────────────────────────────────────────────┘   │   │
│  │                                                  │   │   │
│  │ │ ┌───────────────────────────────────────────────┐   │   │
│  │ │ │   32 GB     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%   │   │
│  │ │ │   28 GB     ━━━━━━━━━━━━━━━━━━━━━━━━━  90%   │   │
│  │ │ │    4 GB     ━━━━━━━━━━━━━━━━━━━━━━━━ 13%   │   │
│  │ │ └───────────────────────────────────────────────┘   │   │
│  │                                                  │   │   │
│  │ │ Time Range: [1h ▼]  Line Chart              │   │
│  │ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Disk I/O (Real-Time)                               │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ Disk sda (SSD 1TB)                           │   │
│  │ │ ┌─ Read: 250 MB/s  ▓▓▓▓▓░░░░░░░░░░░░   │   │
│  │ │ └─ Write: 125 MB/s  ▓▓▓░░░░░░░░░░░░░   │   │   │
│  │ │                                                  │   │   │
│  │ │ ┌─ I/O Wait: 5.2% ───────────────────────────────  │   │
│  │ │ └─ Throughput: 375 MB/s                          │   │   │
│  │ └───────────────────────────────────────────────────────┘   │   │
│  │                                                  │   │   │
│  │ │ Disk sdb (HDD 4TB)                           │   │
│  │ │ ┌─ Read: 50 MB/s   ▓░░░░░░░░░░░░░░░   │   │   │
│  │ │ └─ Write: 25 MB/s   ▓░░░░░░░░░░░░░░   │   │   │
│  │ └───────────────────────────────────────────────────────┘   │   │
│  │                                                  │   │   │
│  │ │ Time Range: [1h ▼]  Line Chart              │   │
│  │ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Network I/O (Real-Time)                           │   │
│  │ ┌───────────────────────────────────────────────────────┐  │   │
│  │ │ eth0 (Public: 192.168.1.100)              │   │
│  │ │ ┌─ RX: 125 Mbps  ▓▓▓▓░░░░░░░░░░░░░░░░   │   │
│  │ │ └─ TX: 45 Mbps   ▓▓░░░░░░░░░░░░░░░░   │   │   │
│  │ │                                                  │   │   │
│  │ │ eth1 (Private: 10.0.0.5)                   │   │
│  │ │ ┌─ RX: 5 Gbps  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │   │
│  │ │ └─ TX: 2.5 Gbps  ▓▓▓▓▓▓▓▓▓▓▓▓▓   │   │
│  │ └───────────────────────────────────────────────────────┘   │   │
│  │                                                  │   │   │
│  │ │ Total Throughput: 5.2 Gbps                     │   │   │
│  │ Time Range: [1h ▼]  Line Chart              │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Per-core CPU gauges** with color-coded thresholds
- **Overall CPU usage** as horizontal progress bar
- **Time range selector:** 1h, 6h, 24h, 7d, 30d
- **Line charts** with smooth animations (using Chart.js or ECharts)
- **Sparklines** for history (last data points shown as mini chart)
- **Progress bars** for memory with color coding
- **I/O bars** for disk/network with directional indicators
- **Real-time updates:** All values update live via SSE

---

### 4. Services Tab (Real-Time)

**Purpose:** Service status, controls, real-time state changes

```
┌─────────────────────────────────────────────────────────────────────┐
│  Search: [                        🔍]  Status: [All ▼]  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Service Name          Status    Last Checked    Actions      │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ nginx               ● Running   2m ago      [⏸][▶️][🔄]  │   │
│  │ mysql               ● Running   2m ago      [⏸][▶️][🔄]  │   │
│  │ redis               ● Running   2m ago      [⏸][▶️][🔄]  │   │
│  │ docker              ● Running   1m ago      [⏸][▶️][🔄]  │   │
│  │ php-fpm             ⏸️ Stopped   1h ago      [▶️][🔄]      │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ cron                ● Running   5m ago      [⏸][▶️][🔄]  │   │
│  │ sshd                ● Running   5m ago      [⏸][▶️][🔄]  │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ...                                       │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ postgresql           ● Running   2m ago      [⏸][▶️][🔄]  │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Status badges:** Green (●) = Running, Gray (⏸) = Stopped, Red (✕) = Failed
- **Last checked:** Relative time with color degradation
- **Actions:**
  - ⏸ (Stop)
  - ▶️ (Start)
  - 🔄 (Restart)
  - ⏭ (View logs)
- **Real-time updates:** Status changes flash via SSE
- **Status filter:** All / Running / Stopped / Failed
- **Bulk actions:** Restart all, Stop all

---

### 5. Processes Tab (Real-Time)

**Purpose:** Process list with resource usage, sorting, filtering

```
┌─────────────────────────────────────────────────────────────────────┐
│  Search: [                              🔍]  Count: 342   │
│  Filter: [All ▼]  Sort: [CPU % ▼]  Refresh: [🔄]      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ PID  Name              User   CPU%  Mem%  State   Actions   │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 1    systemd         root   0.1  0.1  S        ┌─ 🗑─┐ │   │
│  │ 8    nginx            www     2.5  5.2  S        ┌─ 🗑─┐ │   │
│  │ 12   nginx: worker    www     1.2  8.3  S        ┌─ 🗑─┐ │   │
│  │ 1234 mysql           mysql   15.2 32.1  S        ┌─ 🗑─┐ │   │
│  │ 5678 postgres       postgres 8.7  24.5  S        ┌─ 🗑─┐ │   │
│  │ 8902 redis-server     redis   0.5  0.3  S        ┌─ 🗑─┐ │   │
│  │ ...                                             │   │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 12345 python3         python  35.8  15.2  S        ┌─ 🗑─┐ │   │
│  │ 12992 chrome          www-data 12.5  8.2  S        ┌─ 🗑─┐ │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Process state icons:** S = Sleeping, R = Running, D = I/O wait, Z = Zombie
- **Color-coded columns:** CPU/Mem % with background colors (green < 50%, yellow < 70%, red > 70%)
- **Sorting:** CPU %, Mem %, PID, Name, User
- **Filtering:** All / Running / Sleeping / Zombie
- **Actions:** Kill process (with confirmation dialog)
- **Real-time updates:** List refreshes via SSE (throttled to 1 update/sec)
- **Pagination:** 100 processes per page

---

### 6. Packages Tab

**Purpose:** Installed packages, version info, update notifications

```
┌─────────────────────────────────────────────────────────────────────┐
│  Search: [                              🔍]  Updates: 3 [↓]  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Name                  Version    Arch     Source   Update     │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ nginx                 1.24.0     amd64    apt      ⬆️ 1.24.1 │   │
│  │ mysql                 8.0.35     amd64    apt      ✅         │   │
│  │ postgresql            15.3       amd64    apt      ⬆️ 15.4      │   │
│  │ redis                 7.2.4      amd64    apt      ✅         │   │
│  │ python3               3.12.0     amd64    apt      ⬆️ 3.13.0    │   │
│  │ docker-ce              24.0.7     amd64    apt      ⬆️ 24.0.9    │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ...                                             │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ nodejs                18.19.0    amd64    npm      ⬆️ 20.11.0   │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ └─────────────────────────────────────────────────────── │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Bulk Actions:                                    [Update All]  │
│  Refresh:                                        [🔄]       │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Update indicators:** ⬆️ (update available), ✅ (up to date)
- **Version highlighting:** Current version in bold
- **Source badges:** apt, yum, dnf, pacman, npm, etc.
- **Architecture:** amd64, arm64, x86_64
- **Bulk update:** Update all packages (with confirmation)
- **Refresh:** Sync package lists
- **Filter:** Search by name, filter by update status
- **Pagination:** 100 packages per page

---

### 7. Logs Tab (Real-Time)

**Purpose:** Log entries with filtering, search, real-time updates

```
┌─────────────────────────────────────────────────────────────────────┐
│  Level: [All ▼]  Source: [All ▼]  Search: [     🔍]  Tail     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Timestamp              Level   Source    Message            │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 2026-04-17 12:15:23   INFO    nginx     [GET] /api/v1/users │   │
│  │ 200 OK                                    │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 2026-04-17 12:15:24   INFO    nginx     [GET] /api/v1/servers │   │
│  │ 200 OK                                    │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 2026-04-17 12:15:25   INFO    mysql     SELECT * FROM users WHERE  │   │
│  │ 200 OK (123 rows)                          │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 2026-04-17 12:15:30   WARN    redis     Memory usage > 80%  │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 2026-04-17 12:15:31   ERROR    nginx     [error] Connection refused     │   │
│  │                                          │   │
│  │ ...                                             │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 2026-04-17 12:16:00   INFO    cron     [job 1234] Completed successfully  │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Level color coding:** INFO (blue), WARN (yellow), ERROR (red), DEBUG (gray)
- **Source badges:** nginx, mysql, redis, cron, etc.
- **Timestamp:** Human-readable relative time (2m ago)
- **Auto-scroll:** When tailing logs, auto-scroll to bottom
- **Filters:**
  - Level (All, INFO, WARN, ERROR)
  - Source (All services, select specific)
  - Time range (last 1h, 6h, 24h)
- **Search:** Full-text search across all log entries
- **Download:** Export logs as JSON or text file
- **Real-time updates:** New logs appear at top via SSE

---

### 8. Alerts Tab (Real-Time)

**Purpose:** Alert notifications with severity, acknowledgment, filtering

```
┌─────────────────────────────────────────────────────────────────────┐
│  Severity: [All ▼]  Type: [All ▼]  Search: [     🔍] │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Time   Severity  Type        Server   Message            │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 12:15  🚨 Critical  cpu_alert   web01    CPU > 90% (95.2%)  │   │
│  │        [Ack] [View]                              │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 12:10  ⚠️  Warning   mem_alert  web01    Memory > 80% (85.3%)  │   │
│  │        [Ack] [View]                              │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 12:05  🚨 Critical  disk_alert  db01     /var usage > 95% (97.2%) │   │
│  │        [Ack] [View]                              │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 12:00  ℹ️  Info      service   web01    nginx service stopped     │   │
│  │        [Ack] [View]                              │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ...                                             │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ 11:55  🚨 Critical  load_alert  api-01   Load avg 15min > 32      │   │
│  │        [Ack] [View]                              │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ ──────────────────────────────────────────────────────── │   │
│  │ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Visual Features:**
- **Severity icons:** 🚨 (Critical), ⚠️ (Warning), ℹ️ (Info)
- **Color-coded rows:** Red for critical, yellow for warning, blue for info
- **Timestamp:** Human-readable relative time
- **Actions:**
  - Acknowledge (mark as read)
  - View details
  - Filter by severity
  - Filter by type
- **Real-time updates:** New alerts appear at top with flash animation
- **Sound/notification:** Optional sound or browser notification for critical alerts
- **Alert summary:** "5 Critical, 3 Warning, 12 Info" badge

---

## Component Hierarchy

### Vue 3 Component Structure

```
frontend/src/views/servers/detail/
├── index.vue              # Main layout, tabs, header
├── components/
│   ├── ServerHeader.vue   # Server info, status, actions
│   ├── Overview.vue       # Static info (grains)
│   ├── Metrics.vue        # Real-time charts, gauges
│   ├── Services.vue       # Service list, controls
│   ├── Processes.vue       # Process list with sorting
│   ├── Packages.vue       # Package list, updates
│   ├── Logs.vue          # Log entries with filtering
│   └── Alerts.vue        # Alert list, acknowledgments
└── composables/
    └── useSaltStream.ts  # SSE subscriptions (metrics, alerts, services, processes, logs)
```

---

## Real-Time Update Strategy

### SSE Event Handling

```typescript
// composables/useSaltStream.ts

// Subscription management
const subscriptions = {
  metrics: null as EventSource | undefined,
  alerts: null as EventSource | undefined,
  services: null as EventSource | undefined,
  processes: null as EventSource | undefined,
  packages: null as EventSource | undefined,
  logs: null as EventSource | undefined
}

// Update handlers
const handleMetricUpdate = (data: Metric) => {
  // Update local state
  metrics[data.metric_name] = data
  
  // Debounce chart updates (don't re-render on every metric)
  debouncedChartUpdate(data)
}

const handleAlert = (alert: Alert) => {
  // Add to alerts list (newest first)
  alerts.unshift(alert)
  
  // Show notification for critical alerts
  if (alert.severity === 'critical') {
    showBrowserNotification(alert.message)
  }
  
  // Play sound (if enabled)
  if (alert.severity === 'critical' && userSettings.soundEnabled) {
    playCriticalSound()
  }
}

const handleServiceState = (state: ServiceState) => {
  // Update service state
  services[state.service_name] = state.status
  
  // Update status badge in service list
  servicesList.updateServiceStatus(state.service_id, state.status)
}

const handleProcessUpdate = (process: Process) => {
  // Update process list
  processes.update(process)
  
  // Trigger notification if high CPU/Mem
  if (process.cpu_percent > 80 || process.memory_percent > 80) {
    showAlert(`High resource usage: ${process.name} (${process.cpu_percent}% CPU)`)
  }
}
```

### Update Frequency & Throttling

| Data Type | SSE Update Frequency | UI Update Frequency | Strategy |
|-----------|-------------------|-------------------|-----------|
| **Metrics** | Every 30s | 500ms (debounce) | Smooth animations |
| **Alerts** | On event | Immediate | Flash + notification |
| **Services** | On state change | Immediate | Status badge update |
| **Processes** | Every 10s | 1s (throttled) | Don't overwhelm UI |
| **Packages** | On check | Immediate | Update list |
| **Logs** | On new log | 1s (throttled) | Don't overwhelm UI |

---

## Mobile Responsive Design

### Desktop (> 1200px)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Header]                                             │
│  ┌──────────────────┬──────────────────┬──────────────────┐  │
│  │  Overview       │  Metrics        │  Services       │  │
│  │  (Full grains)  │  (3 charts)     │  (Service list)  │  │
│  │  300px height   │  300px height   │  300px height   │  │
│  └──────────────────┴──────────────────┴──────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  [Main Content Area - 600px height]           │  │
│  │  ┌──────────────────┬──────────────────┐        │
│  │  │               │                │        │
│  │  │               │                │        │
│  │  │               │                │        │
│  │  └──────────────────┴──────────────────┘        │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│  [Action Bar]                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Tablet (768px - 1200px)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Header]                                             │
│  ┌──────────────────┬──────────────────┬──────────────────┐  │
│  │  Overview       │  Metrics        │  Services       │  │
│  │  (Full)         │  (2 charts)      │  (List view)     │  │
│  └──────────────────┴──────────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Mobile (< 768px)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Header]                                             │
│  [Server Info - 200px]                                  │
│  [Status Badge ● Online]                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  [Tabs - Scrollable horizontal]                               │
│  [Overview] [Metrics] [Services] [Processes] [Packages]      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  [Main Content - Full width]                                │
│  ┌───────────────────────────────────────────────────────┐        │
│  │  [Content for selected tab]                   │        │
│  │  [Vertical scroll]                              │        │
│  │  [Responsive cards]                           │        │
│  └───────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Accessibility

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + R` | Refresh all data |
| `Ctrl + F` | Focus search |
| `Ctrl + /` | Quick command palette |
| `Escape` | Close modal/drawer |
| `Arrow Keys` | Navigate list/table |
| `Space` | Expand/collapse card |

### Screen Reader Support

- All interactive elements have `aria-label` attributes
- Charts include `<title>` and `<desc>` tags
- Status indicators use `aria-live="polite"` for real-time updates
- Alerts use `role="alert"` and `aria-live="assertive"`

### Color Contrast

- All text meets WCAG 2.1 AA standard (4.5:1 contrast ratio)
- Color-blind friendly: Use symbols (●, ⚠️, 🚨) in addition to color
- Focus indicators: Visible for keyboard navigation

---

## State Management

### Pinia Store Structure

```typescript
// frontend/src/stores/salt.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSaltStore = defineStore('salt', () => {
  // Server static data
  const grains = ref<Grains>({})
  const minionStatus = ref<MinionStatus>({ lastSeen: null })

  // Metrics (real-time)
  const metrics = ref<Record<string, Metric>>({})
  const metricsHistory = ref<Record<string, Metric[]>>({})

  // Services
  const services = ref<Record<string, ServiceState>>({})

  // Processes
  const processes = ref<Process[]>([])

  // Packages
  const packages = ref<Package[]>([])
  const packageUpdates = ref<number>(0)

  // Logs
  const logs = ref<Log[]>([])
  const logTail = ref<Log[]>([])

  // Alerts
  const alerts = ref<Alert[]>([])
  const unreadAlerts = computed(() => alerts.value.filter(a => !a.acknowledged))

  // Connection status
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)

  return {
    grains, minionStatus,
    metrics, metricsHistory,
    services, processes, packages, packageUpdates,
    logs, logTail,
    alerts, unreadAlerts,
    isConnected, reconnectAttempts,

    // Actions
    updateMetric: (serverId: string, metric: Metric) => {
      metrics.value[`${serverId}_${metric.metric_name}`] = metric
      // Add to history
      if (!metricsHistory.value[serverId]) {
        metricsHistory.value[serverId] = []
      }
      metricsHistory.value[serverId].push(metric)
      // Keep only last 1000 per server
      if (metricsHistory.value[serverId].length > 1000) {
        metricsHistory.value[serverId] = metricsHistory.value[serverId].slice(-1000)
      }
    },
    addAlert: (alert: Alert) => {
      alerts.value.unshift(alert)
    },
    acknowledgeAlert: (alertId: string) => {
      const alert = alerts.value.find(a => a.id === alertId)
      if (alert) {
        alert.acknowledged = true
      }
    },
    updateServiceState: (serverId: string, serviceName: string, status: string) => {
      services.value[`${serverId}_${serviceName}`] = { status }
    },
  }
})
```

---

## Performance Optimizations

### 1. Virtual Scrolling

**Problem:** 5000+ process entries would crash the browser.

**Solution:** Use virtual scrolling with window size of 100 items.

```vue
<template>
  <div class="process-list-container">
    <div
      class="virtual-scroller"
      style="height: 600px; overflow-y: auto;"
      @scroll="handleScroll"
    >
      <div v-for="process in visibleProcesses" :key="process.pid">
        <ProcessRow :process="process" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const visibleProcesses = ref([])
const startIndex = ref(0)
const windowSize = 100

const handleScroll = (e) => {
  const container = e.target as HTMLElement
  const scrollTop = container.scrollTop
  const itemHeight = 30 // Process row height

  const newStartIndex = Math.floor(scrollTop / itemHeight)
  startIndex.value = newStartIndex
}

watch(startIndex, () => {
  visibleProcesses.value = processes.value.slice(startIndex.value, startIndex.value + windowSize)
})
</script>
```

### 2. Chart Debouncing

**Problem:** 30-second SSE updates cause excessive re-renders.

**Solution:** Debounce chart updates to once every 500ms.

```typescript
import { debounce } from 'lodash-es'

const debouncedUpdateChart = debounce((data) => {
  chart.updateSeries([data])
}, 500)

watch(() => useSaltStream().metrics, (newMetrics) => {
  Object.values(newMetrics).forEach(debouncedUpdateChart)
})
```

### 3. Log Throttling

**Problem:** 1000+ log entries per minute would overwhelm the DOM.

**Solution:** Only show last 100 log entries, discard older ones.

```typescript
const MAX_LOGS = 100

watch(() => useSaltStream().logs, (newLogs) => {
  logs.value = [...newLogs, ...logs.value].slice(0, MAX_LOGS)
})
```

### 4. Connection Pooling

**Problem:** 500 concurrent SSE connections would overwhelm the server.

**Solution:** Close SSE connections when tab is not visible.

```typescript
const { isActive, pause, resume } = useVisibility()

watch(isActive, (active) => {
  if (!active) {
    pause() // Close SSE connections
  } else {
    resume() // Reconnect SSE connections
  }
})
```

---

## Visual Polish

### 1. Animations

| Animation | Duration | Purpose |
|-----------|----------|---------|
| **Chart updates** | 300ms | Smooth line transitions |
| **Alert flash** | 500ms | Get attention |
| **Status change** | 200ms | Smooth badge transition |
| **New list items** | 200ms | Fade in from top |
| **Loading skeletons** | 1500ms | Show before data arrives |

### 2. Loading States

**Metrics (before data arrives):**

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────┐   │
│  │ CPU Usage                                     │   │
│  │ ┌───────────────────────────────────────────────┐   │   │
│  │ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │   │
│  │ │ ▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░  │   │   │
│  │ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │   │
│  │ └───────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────┘   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Memory Usage                                       │   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │   32 GB     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 90%   │   │
│  │    4 GB     ━━━━━━━━━━━━━━━━━━━━━━━━━━ 13%   │   │
│  │ └───────────────────────────────────────────────────────┘   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Empty States

**Services (none installed):**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────────────────────────────────────────────────┐        │
│  │         No services detected on this server          │        │
│  │                                                         │        │
│  │         [Rescan Services] [Run System Check]       │        │
│  │                                                         │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

**Logs (no logs in range):**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────────────────────────────────────────────────┐        │
│  │         No logs found in the last 1 hour        │        │
│  │                                                         │        │
│  │         [Expand Time Range] [Download Logs]      │        │
│  │                                                         │        │
│  │         [Auto-refresh: ON  (30s)               │        │
│  │                                                         │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Ready for Implementation

**UI/UX Design Status:** ✅ Complete

**What's Included:**
- ✅ Overall layout strategy
- ✅ Professional color scheme
- ✅ Typography guidelines
- ✅ 8 detailed component designs (wireframes)
- ✅ Real-time update strategy
- ✅ Mobile responsive layouts
- ✅ Accessibility features
- ✅ State management structure
- ✅ Performance optimizations
- ✅ Visual polish (animations, loading states)

**Next Step:** Proceed with Phase 4 - Backend Implementation

---

**Related Enhancements:**
- `002-saltstack-implementation-full.md` - Full implementation plan

**Related Issues:**
- None yet

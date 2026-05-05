#!/usr/bin/env python3
"""OpsPilot push agent — minimal deps (stdlib only)."""
from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("OPSPILOT_AGENT_CONFIG", "/opt/opspilot/config/agent.json"))


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _read_mem() -> tuple[int, int]:
    total_kb = avail_kb = 0
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total_kb = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    avail_kb = int(line.split()[1])
    except OSError:
        pass
    return total_kb, avail_kb


def _read_loadavg() -> list[str]:
    try:
        with open("/proc/loadavg", encoding="utf-8") as f:
            return f.read().split()[:3]
    except OSError:
        return ["0.0", "0.0", "0.0"]


def _read_cpu_detail() -> dict:
    """Two-sample /proc/stat 350ms apart → overall + breakdown + per-core metrics."""
    def _read_stat_lines():
        lines = {}
        try:
            with open("/proc/stat", encoding="utf-8") as f:
                for line in f:
                    if not line.startswith("cpu"):
                        break
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    vals = [int(x) for x in parts[1:9]]
                    while len(vals) < 8:
                        vals.append(0)
                    lines[parts[0]] = vals
        except OSError:
            pass
        return lines

    a = _read_stat_lines()
    time.sleep(0.35)
    b = _read_stat_lines()

    result: dict = {
        "cpu_percent": 0.0, "cpu_usage": 0.0,
        "cpu_total_user": 0.0, "cpu_total_system": 0.0,
        "cpu_total_iowait": 0.0, "cpu_total_idle": 0.0,
    }
    for name, bvals in b.items():
        avals = a.get(name)
        if not avals:
            continue
        d = [bvals[i] - avals[i] for i in range(8)]
        total = sum(d)
        if total <= 0:
            continue
        # /proc/stat fields: user nice system idle iowait irq softirq steal
        overall = round(100.0 * (total - d[3]) / total, 2)
        if name == "cpu":
            result["cpu_percent"] = overall
            result["cpu_usage"] = overall
            result["cpu_total_user"]   = round(100.0 * (d[0] + d[1]) / total, 2)
            result["cpu_total_system"] = round(100.0 * d[2] / total, 2)
            result["cpu_total_iowait"] = round(100.0 * d[4] / total, 2)
            result["cpu_total_idle"]   = round(100.0 * d[3] / total, 2)
        else:
            core_id = name[3:]  # "cpu0" → "0"
            result[f"cpu_{core_id}_user"] = overall
    return result


_SKIP_FSTYPES = {
    "tmpfs", "devtmpfs", "sysfs", "proc", "devpts", "cgroup", "cgroup2",
    "pstore", "debugfs", "securityfs", "hugetlbfs", "mqueue", "fusectl",
    "tracefs", "binfmt_misc", "overlay", "squashfs", "autofs",
}
_SKIP_PREFIXES = ("/proc", "/sys", "/dev", "/run")


def _collect_disk_mounts() -> list:
    """Return per-mount disk stats. Falls back to '/' only on error."""
    seen: set = set()
    mounts = []
    try:
        with open("/proc/mounts", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            parts = line.split()
            if len(parts) < 3:
                continue
            device, mountpoint, fstype = parts[0], parts[1], parts[2]
            if fstype in _SKIP_FSTYPES:
                continue
            if any(mountpoint.startswith(p) for p in _SKIP_PREFIXES):
                continue
            if mountpoint in seen:
                continue
            seen.add(mountpoint)
            try:
                st = os.statvfs(mountpoint)
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                used = total - free
                if total <= 0:
                    continue
                mounts.append({
                    "mountpoint": mountpoint,
                    "device": device,
                    "fstype": fstype,
                    "used_bytes": used,
                    "total_bytes": total,
                    "used_percent": round(100.0 * used / total, 2),
                })
            except OSError:
                continue
    except OSError:
        pass
    if not mounts:
        try:
            st = os.statvfs("/")
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            used = total - free
            if total > 0:
                mounts.append({"mountpoint": "/", "device": "", "fstype": "",
                                "used_bytes": used, "total_bytes": total,
                                "used_percent": round(100.0 * used / total, 2)})
        except OSError:
            pass
    return mounts


def _uptime_seconds() -> int:
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            return int(float(f.read().split()[0]))
    except OSError:
        return 0


def _cpu_cores() -> int | None:
    try:
        count = sum(1 for line in open("/proc/cpuinfo") if line.startswith("processor"))
        return count or None
    except OSError:
        return None


def _cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


def _timezone() -> str:
    try:
        with open("/etc/timezone", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        pass
    try:
        out = subprocess.check_output(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            timeout=5, stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        pass
    return "UTC"


def _read_dmi(filename: str) -> str:
    try:
        with open(f"/sys/devices/virtual/dmi/id/{filename}", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _detect_virtual() -> tuple:
    sys_vendor = _read_dmi("sys_vendor").lower()
    _VIRT_MAP = [
        ("vmware", "vmware"), ("virtualbox", "virtualbox"), ("innotek", "virtualbox"),
        ("kvm", "kvm"), ("qemu", "kvm"), ("xen", "xen"),
        ("microsoft corporation", "hyperv"), ("bochs", "kvm"),
    ]
    for kw, vtype in _VIRT_MAP:
        if kw in sys_vendor:
            return True, vtype
    try:
        out = subprocess.check_output(
            ["systemd-detect-virt", "--quiet"], timeout=3, stderr=subprocess.DEVNULL,
        )
        vtype = out.decode().strip()
        if vtype and vtype != "none":
            return True, vtype
    except Exception:
        pass
    return False, ""


_CLOUD_DMI_MAP = {
    "amazon ec2": "aws", "amazon": "aws",
    "digitalocean": "digitalocean",
    "google": "gcp",
    "microsoft corporation": "azure",
    "hetzner": "hetzner",
    "linode": "linode",
    "vultr": "vultr",
    "ovh": "ovh",
}


def _detect_cloud() -> dict:
    sys_vendor = _read_dmi("sys_vendor").lower()
    board_vendor = _read_dmi("board_vendor").lower()
    product_name = _read_dmi("product_name").lower()

    provider = ""
    for key, val in _CLOUD_DMI_MAP.items():
        if key in sys_vendor or key in board_vendor:
            provider = val
            break
    if not provider and "google" in product_name:
        provider = "gcp"

    result: dict = {"cloud_provider": provider or "unknown", "cloud_region": "", "cloud_instance_type": ""}
    if not provider:
        return result

    def _imds(url: str, headers: dict | None = None) -> str:
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=0.5) as r:
                return r.read().decode().strip()
        except Exception:
            return ""

    if provider == "aws":
        result["cloud_region"] = _imds("http://169.254.169.254/latest/meta-data/placement/region")
        result["cloud_instance_type"] = _imds("http://169.254.169.254/latest/meta-data/instance-type")
    elif provider == "digitalocean":
        result["cloud_region"] = _imds("http://169.254.169.254/metadata/v1/region")
        result["cloud_instance_type"] = _imds("http://169.254.169.254/metadata/v1/droplet/size_slug")
    elif provider == "gcp":
        gcp_h = {"Metadata-Flavor": "Google"}
        zone = _imds("http://169.254.169.254/computeMetadata/v1/instance/zone", gcp_h)
        if zone:
            result["cloud_region"] = "-".join(zone.split("/")[-1].split("-")[:-1])
        mt = _imds("http://169.254.169.254/computeMetadata/v1/instance/machine-type", gcp_h)
        result["cloud_instance_type"] = mt.split("/")[-1] if mt else ""
    elif provider == "azure":
        raw = _imds(
            "http://169.254.169.254/metadata/instance/compute?api-version=2021-02-01",
            {"Metadata": "true"},
        )
        if raw:
            try:
                data = json.loads(raw)
                result["cloud_region"] = data.get("location", "")
                result["cloud_instance_type"] = data.get("vmSize", "")
            except Exception:
                pass
    elif provider == "hetzner":
        result["cloud_region"] = _imds("http://169.254.169.254/hetzner/v1/metadata/region")

    return result


def _collect_network_interfaces() -> list:
    try:
        out = subprocess.check_output(
            ["ip", "-o", "addr"], timeout=5, stderr=subprocess.DEVNULL,
        ).decode(errors="replace")
        ifaces: dict = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            iface = parts[1].rstrip(":")
            family = parts[2]
            addr = parts[3]
            if iface not in ifaces:
                ifaces[iface] = {
                    "iface": iface, "mac": "", "ipv4": "", "ipv4_prefix": "",
                    "ipv6": "", "ipv6_prefix": "", "is_up": True,
                }
            if family == "inet":
                ip, prefix = (addr.split("/") + ["24"])[:2]
                ifaces[iface]["ipv4"] = ip
                ifaces[iface]["ipv4_prefix"] = prefix
            elif family == "inet6" and not addr.startswith("fe80"):
                ip6, prefix6 = (addr.split("/") + ["64"])[:2]
                ifaces[iface]["ipv6"] = ip6
                ifaces[iface]["ipv6_prefix"] = prefix6
        for iface in ifaces:
            try:
                with open(f"/sys/class/net/{iface}/address", encoding="utf-8") as f:
                    ifaces[iface]["mac"] = f.read().strip()
            except OSError:
                pass
            try:
                with open(f"/sys/class/net/{iface}/operstate", encoding="utf-8") as f:
                    ifaces[iface]["is_up"] = f.read().strip() in ("up", "unknown")
            except OSError:
                pass
        return list(ifaces.values())
    except Exception:
        return []


def _primary_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return ""


def _os_info() -> tuple[str, str]:
    name = version = ""
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ID="):
                    name = line[3:].strip('"\'')
                elif line.startswith("VERSION_ID="):
                    version = line[11:].strip('"\'')
    except OSError:
        name = platform.system().lower()
        version = platform.release()
    return name, version


def _collect_processes(top_n: int = 20) -> list:
    """Top N processes by CPU via ps aux + etimes. Returns [] on any failure."""
    elapsed_map: dict = {}
    try:
        et_out = subprocess.check_output(
            ["ps", "-eo", "pid=,etimes="],
            timeout=5,
            stderr=subprocess.DEVNULL,
        ).decode(errors="replace")
        for et_line in et_out.splitlines():
            et_parts = et_line.split()
            if len(et_parts) == 2:
                try:
                    elapsed_map[int(et_parts[0])] = int(et_parts[1])
                except ValueError:
                    pass
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["ps", "aux"],
            timeout=10,
            stderr=subprocess.DEVNULL,
        ).decode(errors="replace")
        lines = out.splitlines()
        if lines and lines[0].lstrip().startswith("USER"):
            lines = lines[1:]
        procs = []
        now_epoch = int(time.time())
        for line in lines:
            parts = line.split(None, 10)
            if len(parts) < 11:
                continue
            try:
                pid = int(parts[1])
                cmd = parts[10].strip()
                elapsed_s = elapsed_map.get(pid, 0)
                start_epoch = now_epoch - elapsed_s
                start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_epoch))
                procs.append({
                    "pid": pid,
                    "username": parts[0][:32],
                    "cpu_percent": float(parts[2]),
                    "memory_percent": float(parts[3]),
                    "memory_rss_kb": int(parts[5]),
                    "state": (parts[7][:1] if parts[7] else "S"),
                    "name": (cmd.split("/")[-1].split()[0])[:80] if cmd else "",
                    "command": cmd[:200],
                    "start_time": start_iso,
                })
            except (ValueError, IndexError):
                continue
        procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
        return procs[:top_n]
    except Exception:
        return []


def _collect_services() -> dict:
    """Service states via systemctl. Returns dict[unit, {status,sub_state,enabled,description}]."""
    try:
        out = subprocess.check_output(
            ["systemctl", "list-units", "--type=service", "--no-legend", "--no-pager", "--all"],
            timeout=15,
            stderr=subprocess.DEVNULL,
        ).decode(errors="replace")
        services = {}
        for line in out.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 4:
                continue
            name = parts[0]
            if not name.endswith(".service"):
                continue
            active = parts[2]   # active / inactive / failed
            sub    = parts[3]   # running / dead / failed / exited / waiting
            desc   = parts[4].strip() if len(parts) > 4 else ""
            if active == "active" and sub == "running":
                status = "running"
            elif active == "failed" or sub == "failed":
                status = "failed"
            else:
                status = "stopped"
            services[name] = {"status": status, "sub_state": sub, "description": desc}

        # Enrich with enabled state
        try:
            uf_out = subprocess.check_output(
                ["systemctl", "list-unit-files", "--type=service", "--no-legend", "--no-pager"],
                timeout=10,
                stderr=subprocess.DEVNULL,
            ).decode(errors="replace")
            for line in uf_out.splitlines():
                uf_parts = line.split()
                if len(uf_parts) < 2:
                    continue
                if uf_parts[0] in services:
                    services[uf_parts[0]]["enabled"] = uf_parts[1]
        except Exception:
            pass

        return services
    except Exception:
        return {}


_KNOWN_LOG_PATHS = [
    ("/var/log/syslog", "syslog"),
    ("/var/log/messages", "messages"),
    ("/var/log/auth.log", "auth"),
    ("/var/log/secure", "auth"),
    ("/var/log/nginx/error.log", "nginx"),
    ("/var/log/apache2/error.log", "apache2"),
    ("/var/log/httpd/error_log", "httpd"),
    ("/var/log/mysql/error.log", "mysql"),
]


def _collect_logs(max_lines: int = 150) -> list:
    """Collect recent logs: journalctl JSON (primary) → known log files (fallback)."""
    entries: list = []

    # Primary: journalctl --output=json covers ALL systemd services universally
    try:
        result = subprocess.run(
            ["journalctl", "--since", "35 seconds ago", "--output=json", "--no-pager", "-n", str(max_lines)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ts_usec = int(obj.get("__REALTIME_TIMESTAMP") or 0)
                    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_usec / 1_000_000)) if ts_usec else None
                    priority = int(obj.get("PRIORITY") or 6)
                    level = "ERROR" if priority <= 3 else "WARN" if priority == 4 else "DEBUG" if priority >= 7 else "INFO"
                    unit = obj.get("_SYSTEMD_UNIT") or obj.get("SYSLOG_IDENTIFIER") or "system"
                    source = unit.replace(".service", "").replace(".timer", "").replace(".socket", "")
                    msg = obj.get("MESSAGE") or ""
                    if isinstance(msg, list):
                        msg = " ".join(str(x) for x in msg)
                    entries.append({
                        "timestamp": ts,
                        "level": level,
                        "source": str(source)[:200],
                        "message": str(msg)[:4000],
                    })
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # Fallback: tail known log files when journalctl unavailable (non-systemd)
    if not entries:
        for path, source in _KNOWN_LOG_PATHS:
            try:
                with open(path, "r", errors="replace") as fh:
                    tail = fh.readlines()[-40:]
                for line in tail:
                    line = line.strip()
                    if not line:
                        continue
                    lo = line.lower()
                    level = "ERROR" if any(w in lo for w in ("error", "crit", "emerg", "alert")) else "WARN" if "warn" in lo else "INFO"
                    entries.append({"timestamp": None, "level": level, "source": source, "message": line[:4000]})
                if len(entries) >= max_lines:
                    break
            except (OSError, PermissionError):
                continue

    return entries[:max_lines]


def collect_host_profile() -> dict:
    os_name, os_version = _os_info()
    total_kb, _ = _read_mem()
    is_virtual, virtual_type = _detect_virtual()
    cloud = _detect_cloud()
    fqdn = socket.getfqdn()
    hostname = socket.gethostname()
    domain = fqdn[len(hostname):].lstrip(".") if fqdn.startswith(hostname) else ""
    return {
        "hostname": hostname,
        "fqdn": fqdn,
        "domain": domain,
        "ip_address": _primary_ip(),
        "os_name": os_name,
        "os_version": os_version,
        "architecture": platform.machine(),
        "cpu_cores": _cpu_cores(),
        "cpu_model": _cpu_model(),
        "memory_mb": (total_kb // 1024) if total_kb else None,
        "kernel": platform.release(),
        "timezone": _timezone(),
        "virtual": is_virtual,
        "virtual_type": virtual_type,
        **cloud,
        "network_interfaces": _collect_network_interfaces(),
    }


def _count_processes() -> int:
    try:
        out = subprocess.check_output(["ps", "ax", "--no-headers"], timeout=5, stderr=subprocess.DEVNULL)
        return len(out.decode(errors="replace").splitlines())
    except Exception:
        return 0


def _count_running_services() -> int:
    try:
        out = subprocess.check_output(
            ["systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--no-pager"],
            timeout=10,
            stderr=subprocess.DEVNULL,
        )
        return sum(1 for line in out.decode(errors="replace").splitlines() if line.strip())
    except Exception:
        return 0


def collect_metrics() -> dict:
    total_kb, avail_kb = _read_mem()
    used_kb = max(0, total_kb - avail_kb)
    mem_pct = round(100.0 * used_kb / total_kb, 2) if total_kb else 0.0
    load = _read_loadavg()
    cpu = _read_cpu_detail()
    disks = _collect_disk_mounts()
    # Keep flat root disk key for backward compat
    root_disk_pct = next((d["used_percent"] for d in disks if d["mountpoint"] == "/"), 0.0)
    return {
        "source": "opspilot-agent",
        "loadavg_1m": float(load[0]),
        "loadavg_5m": float(load[1]) if len(load) > 1 else 0.0,
        "loadavg_15m": float(load[2]) if len(load) > 2 else 0.0,
        "memory_used_percent": mem_pct,
        "memory_percent": mem_pct,
        "disk_usage_percent": root_disk_pct,
        "disk_usage": root_disk_pct,
        "disks": disks,
        "uptime_seconds": _uptime_seconds(),
        "process_count": _count_processes(),
        "service_count": _count_running_services(),
        **cpu,
    }


def post_payload(
    cfg: dict,
    metrics: dict,
    host_profile: dict | None = None,
    processes: list | None = None,
    services: dict | None = None,
    logs: list | None = None,
) -> None:
    base = cfg["api_base_url"].rstrip("/")
    url = f"{base}/servers/{cfg['server_id']}/metrics"
    body_obj: dict = {
        "server_id": cfg["server_id"],
        "organization_id": cfg["organization_id"],
        "metrics": metrics,
    }
    if host_profile:
        body_obj["host_profile"] = host_profile
    if processes is not None:
        body_obj["processes"] = processes
    if services is not None:
        body_obj["services"] = services
    if logs is not None:
        body_obj["logs"] = logs
    req = urllib.request.Request(
        url,
        data=json.dumps(body_obj).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": cfg["api_key"]},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.getcode() not in (200, 201):
            raise RuntimeError(f"unexpected status {resp.getcode()}")


def main() -> None:
    interval = 5
    push_count = 0
    while True:
        try:
            cfg = load_config()
            interval = int(cfg.get("interval_seconds", 60))
            metrics = collect_metrics()
            # host_profile: first push + every 10 (rarely changes)
            profile = collect_host_profile() if push_count % 10 == 0 else None
            # processes: every 3rd push (~15s) — top 20 by CPU
            processes = _collect_processes() if push_count % 3 == 0 else None
            # services: every 6th push (~30s) — rarely change
            services = _collect_services() if push_count % 6 == 0 else None
            # logs: every 6th push (~30s) — rolling 35s window via journalctl
            logs = _collect_logs() if push_count % 6 == 0 else None
            post_payload(cfg, metrics, host_profile=profile, processes=processes, services=services, logs=logs)
            push_count += 1
        except urllib.error.HTTPError as e:
            print(f"opspilot-agent: HTTP error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"opspilot-agent: error: {e}", file=sys.stderr)
        time.sleep(max(2, interval))


if __name__ == "__main__":
    main()

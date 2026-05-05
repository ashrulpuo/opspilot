# -*- coding: utf-8 -*-
"""Push metrics to OpsPilot REST API using pillar ``opspilot``.

Expects pillar (from OpsPilot backend ``pillar.set``): ``api_base_url``, ``server_id``,
``organization_id``, ``api_key`` — same contract as ``/api/v1/servers/{id}/metrics``.

Run manually: ``salt-call opspilot_metrics.push``
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

__virtualname__ = "opspilot_metrics"


def __virtual__():
    return __virtualname__


def _read_stat_cpus():
    """Parse /proc/stat cpu lines -> name -> list of jiffies (first 8 fields)."""
    cpus = {}
    with open("/proc/stat", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("cpu"):
                break
            parts = line.split()
            name = parts[0]
            nums = [int(x) for x in parts[1:9]]
            while len(nums) < 8:
                nums.append(0)
            cpus[name] = nums
    return cpus


def _cpu_percentages(prev: dict, curr: dict) -> dict:
    """Return percent user/system/iowait/idle for aggregate 'cpu' and per-core 'cpuN'."""
    out = {}
    for name, b in curr.items():
        if name not in prev:
            continue
        a = prev[name]
        deltas = [b[i] - a[i] for i in range(8)]
        total = sum(deltas)
        if total <= 0:
            continue
        user_nice = deltas[0] + deltas[1]
        system = deltas[2]
        idle = deltas[3]
        iowait = deltas[4]
        user_pct = round(100.0 * user_nice / total, 2)
        system_pct = round(100.0 * system / total, 2)
        iowait_pct = round(100.0 * iowait / total, 2)
        idle_pct = round(100.0 * idle / total, 2)
        out[name] = {
            "user": user_pct,
            "system": system_pct,
            "iowait": iowait_pct,
            "idle": idle_pct,
            "usage": round(100.0 * (user_nice + system + iowait) / total, 2),
        }
    return out


def _meminfo_bytes() -> dict:
    """MemTotal, MemAvailable, SwapTotal, SwapFree in bytes."""
    mem_total = mem_avail = swap_total = swap_free = 0
    with open("/proc/meminfo", encoding="utf-8") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1]) * 1024
            elif line.startswith("MemAvailable:"):
                mem_avail = int(line.split()[1]) * 1024
            elif line.startswith("SwapTotal:"):
                swap_total = int(line.split()[1]) * 1024
            elif line.startswith("SwapFree:"):
                swap_free = int(line.split()[1]) * 1024
    return {
        "mem_total": mem_total,
        "mem_available": mem_avail,
        "swap_total": swap_total,
        "swap_used": max(0, swap_total - swap_free),
    }


def _loadavg() -> tuple[float, float, float]:
    load = open("/proc/loadavg", encoding="utf-8").read().split()
    if len(load) < 3:
        return 0.0, 0.0, 0.0
    return float(load[0]), float(load[1]), float(load[2])


def _disk_rows() -> list:
    """Physical disk usage via statvfs; skip pseudo filesystems."""
    skip_prefixes = ("proc", "sys", "dev", "run", "snap", "cgroup", "overlay")
    rows = []
    seen = set()
    try:
        with open("/proc/mounts", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                device, mountpoint, fstype = parts[0], parts[1], parts[2]
                if fstype in ("proc", "sysfs", "devtmpfs", "cgroup2", "cgroup", "tmpfs", "squashfs"):
                    continue
                if any(device.startswith(p) for p in ("proc", "sysfs", "cgroup")):
                    continue
                if mountpoint in seen:
                    continue
                seen.add(mountpoint)
                try:
                    st = os.statvfs(mountpoint)
                except OSError:
                    continue
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                if total <= 0:
                    continue
                used = total - free
                used_pct = round(100.0 * used / total, 2)
                rows.append(
                    {
                        "mountpoint": mountpoint,
                        "device": device,
                        "fstype": fstype,
                        "used_percent": used_pct,
                        "used_bytes": int(used),
                        "total_bytes": int(total),
                    }
                )
    except OSError:
        pass
    rows.sort(key=lambda r: len(r["mountpoint"]))
    return rows


def _collect_metrics() -> dict:
    """Structured payload for OpsPilot dashboard (schema_version 2)."""
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    load1, load5, load15 = _loadavg()
    prev = _read_stat_cpus()
    time.sleep(0.35)
    curr = _read_stat_cpus()
    pct = _cpu_percentages(prev, curr)

    agg = pct.get("cpu")
    cores_out: list = []
    num_cores = max(1, sum(1 for k in pct if k.startswith("cpu") and k != "cpu"))
    est_cpu_from_load = min(100.0, round((load1 / num_cores) * 100.0, 2))

    cpu_total_user = agg["user"] if agg else est_cpu_from_load
    cpu_total_system = agg["system"] if agg else 0.0
    cpu_total_iowait = agg["iowait"] if agg else 0.0
    cpu_total_idle = agg["idle"] if agg else max(0.0, 100.0 - est_cpu_from_load)

    for name in sorted(pct.keys()):
        if name == "cpu" or not name.startswith("cpu"):
            continue
        core_id = name.replace("cpu", "")
        if core_id.isdigit():
            cores_out.append(
                {
                    "name": core_id,
                    "usage_percent": pct[name]["usage"],
                }
            )

    if not cores_out and agg:
        cores_out.append({"name": "0", "usage_percent": agg["usage"]})

    mem = _meminfo_bytes()
    mem_total = mem["mem_total"]
    mem_avail = mem["mem_available"]
    used_kb = max(0, mem_total - mem_avail) if mem_total else 0
    memory_used_percent = round(100.0 * used_kb / mem_total, 2) if mem_total else 0.0

    disks = _disk_rows()

    return {
        "schema_version": 2,
        "source": "opspilot-salt-module",
        "collected_at": collected_at,
        "loadavg_1m": load1,
        "loadavg_5m": load5,
        "loadavg_15m": load15,
        "memory_used_percent": memory_used_percent,
        "memory_percent": memory_used_percent,
        "cpu_percent": agg["usage"] if agg else est_cpu_from_load,
        "cpu_total_user": cpu_total_user,
        "cpu_total_system": cpu_total_system,
        "cpu_total_iowait": cpu_total_iowait,
        "cpu_total_idle": cpu_total_idle,
        "mem_total": float(mem_total),
        "mem_available": float(mem_avail),
        "swap_total": float(mem["swap_total"]),
        "swap_used": float(mem["swap_used"]),
        "cpu_cores": cores_out,
        "disks": disks,
        # Dashboard cards still read these keys:
        "cpu_usage": agg["usage"] if agg else est_cpu_from_load,
        "disk_usage_percent": disks[0]["used_percent"] if disks else 0.0,
        "uptime_seconds": _uptime_seconds(),
    }


def _uptime_seconds() -> int:
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            return int(float(f.read().split()[0]))
    except OSError:
        return 0


def collect_metrics() -> dict:
    """Return metrics dict without POST (used by ``opspilot_snapshot.push``)."""
    return _collect_metrics()


def push() -> dict:
    """POST metrics to OpsPilot ``PUBLIC_API_BASE_URL`` for this server."""
    nested = __salt__["pillar.get"]("opspilot", {}) or {}
    pg = __salt__["pillar.get"]
    api_base = (
        nested.get("api_base_url")
        or pg("opspilot:api_base_url", "")
        or ""
    ).rstrip("/")
    server_id = nested.get("server_id") or pg("opspilot:server_id", "")
    org_id = nested.get("organization_id") or pg("opspilot:organization_id", "")
    api_key = nested.get("api_key") or pg("opspilot:api_key", "")

    if not all([api_base, server_id, org_id, api_key]):
        return {
            "ok": False,
            "error": "missing opspilot pillar (need api_base_url, server_id, organization_id, api_key)",
        }

    body = {
        "server_id": server_id,
        "organization_id": org_id,
        "metrics": _collect_metrics(),
    }
    url = f"{api_base}/servers/{server_id}/metrics"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return {"ok": True, "status": resp.getcode()}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:800]
        return {"ok": False, "error": str(e), "detail": err_body}
    except Exception as e:
        return {"ok": False, "error": str(e)}

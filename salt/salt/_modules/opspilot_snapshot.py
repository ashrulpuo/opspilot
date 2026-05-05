# -*- coding: utf-8 -*-
"""Full snapshot push to OpsPilot (metrics + host profile + processes/services/packages/logs).

Uses pillar ``opspilot`` like ``opspilot_metrics.push``. POST body matches extended
``POST /api/v1/servers/{id}/metrics`` (same ``X-API-Key``).

Run: ``salt-call opspilot_snapshot.push``
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request

__virtualname__ = "opspilot_snapshot"


def __virtual__():
    return __virtualname__


def _pillar():
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
    return api_base, server_id, org_id, api_key


def _host_profile_from_grains() -> dict:
    g = dict(__salt__["grains.items"]())
    ips = []
    for key in ("fqdn_ip4", "ipv4"):
        if key in g and g[key]:
            if isinstance(g[key], list):
                ips.extend(str(x) for x in g[key])
            else:
                ips.append(str(g[key]))
    if not ips and "ip4_interfaces" in g and isinstance(g["ip4_interfaces"], dict):
        for _iface, lst in g["ip4_interfaces"].items():
            if isinstance(lst, list):
                ips.extend(str(x) for x in lst if x and str(x) != "127.0.0.1")
    ips = list(dict.fromkeys(ips))[:12]
    mem_mb = None
    if "mem_total" in g:
        try:
            mem_mb = int(int(g["mem_total"]) / (1024 * 1024))
        except (TypeError, ValueError):
            pass
    mem_bytes = None
    if mem_mb is not None:
        mem_bytes = float(mem_mb * 1024 * 1024)
    return {
        "hostname": str(g.get("nodename") or g.get("host") or ""),
        "ips": ips,
        "os_name": str(g.get("os") or ""),
        "os_version": str(g.get("osrelease") or ""),
        "os_pretty": str(g.get("oscodename") or ""),
        "architecture": str(g.get("cpuarch") or g.get("osarch") or ""),
        "cpu_cores": int(g.get("num_cpus") or 0) or None,
        "memory_mb": mem_mb,
        "memory_total_bytes": mem_bytes,
    }


def _run_ps_snapshot() -> list:
    cmd = (
        "ps -eo pid,user,%cpu,%mem,stat,cmd --sort=-%cpu --no-headers 2>/dev/null | "
        "head -n 200"
    )
    try:
        out = subprocess.check_output(cmd, shell=True, timeout=45, stderr=subprocess.DEVNULL)
        text = out.decode(errors="replace")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return []
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        pid_s, user, cpu_s, mem_s, st, cmdline = parts[:6]
        try:
            pid = int(pid_s)
        except ValueError:
            continue
        try:
            cpu_f = float(cpu_s)
            mem_f = float(mem_s)
        except ValueError:
            cpu_f = mem_f = 0.0
        rows.append(
            {
                "pid": pid,
                "name": (cmdline.split()[0] if cmdline else "?")[-64:],
                "cmd": cmdline[:8000],
                "user": user[:128],
                "cpu_percent": cpu_f,
                "mem_percent": mem_f,
                "state": st[:4],
            }
        )
        if len(rows) >= 200:
            break
    return rows


def _systemd_services_snapshot() -> dict:
    cmd = (
        "systemctl list-units --type=service --no-pager --no-legend "
        "2>/dev/null | head -n 250"
    )
    try:
        out = subprocess.check_output(cmd, shell=True, timeout=60, stderr=subprocess.DEVNULL)
        text = out.decode(errors="replace")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return {}
    svc = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        unit = parts[0]
        active = parts[2].lower()
        if not unit.endswith(".service"):
            continue
        name = unit.replace(".service", "")
        if active in ("active", "running"):
            svc[name] = "running"
        elif active in ("inactive", "dead", "failed"):
            svc[name] = "stopped"
        else:
            svc[name] = "unknown"
    return svc


def _pkg_snapshot() -> dict:
    try:
        pkgs = __salt__["pkg.list_pkgs"]()
    except Exception:
        return {}
    if not isinstance(pkgs, dict):
        return {}
    out = {}
    for i, (name, ver) in enumerate(pkgs.items()):
        if i >= 600:
            break
        if isinstance(ver, str):
            out[name] = {"version": ver, "source": "pkg"}
        elif isinstance(ver, dict):
            out[name] = ver
        else:
            out[name] = {"version": str(ver), "source": "pkg"}
    return out


def _journal_tail() -> list:
    cmd = "journalctl -n 25 --no-pager -o short-iso 2>/dev/null"
    try:
        out = subprocess.check_output(cmd, shell=True, timeout=30, stderr=subprocess.DEVNULL)
        text = out.decode(errors="replace")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return []
    logs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        ts = ""
        msg = line
        m = re.match(r"(\S+\s+\S+\s+\S+)\s+(.*)", line)
        if m:
            ts = m.group(1)
            msg = m.group(2)
        logs.append({"timestamp": ts or "", "level": "INFO", "source": "journal", "message": msg[:4000]})
        if len(logs) >= 25:
            break
    return logs


def push() -> dict:
    """POST full snapshot (metrics + host_profile + optional inventories)."""
    api_base, server_id, org_id, api_key = _pillar()
    if not all([api_base, server_id, org_id, api_key]):
        return {
            "ok": False,
            "error": "missing opspilot pillar (need api_base_url, server_id, organization_id, api_key)",
        }

    fn = __salt__.get("opspilot_metrics.collect_metrics")
    if not fn:
        return {
            "ok": False,
            "error": "opspilot_metrics not loaded; run: salt-call saltutil.sync_modules",
        }
    metrics = fn()
    body = {
        "server_id": server_id,
        "organization_id": org_id,
        "metrics": metrics,
        "host_profile": _host_profile_from_grains(),
        "processes": _run_ps_snapshot(),
        "services": _systemd_services_snapshot(),
        "packages": _pkg_snapshot(),
        "logs": _journal_tail(),
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            return {"ok": True, "status": resp.getcode()}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:1200]
        return {"ok": False, "error": str(e), "detail": err_body}
    except Exception as e:
        return {"ok": False, "error": str(e)}

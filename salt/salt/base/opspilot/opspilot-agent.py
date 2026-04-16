#!/usr/bin/env python3
"""OpsPilot push agent — minimal deps (stdlib only)."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("OPSPILOT_AGENT_CONFIG", "/opt/opspilot/config/agent.json"))


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _read_mem_kb() -> tuple[int, int]:
    mem_total_kb = 0
    mem_avail_kb = 0
    with open("/proc/meminfo", encoding="utf-8") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                mem_total_kb = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                mem_avail_kb = int(line.split()[1])
    return mem_total_kb, mem_avail_kb


def _read_loadavg() -> list[str]:
    with open("/proc/loadavg", encoding="utf-8") as f:
        return f.read().split()[:3]


def collect_metrics() -> dict:
    mem_total_kb, mem_avail_kb = _read_mem_kb()
    used_kb = max(0, mem_total_kb - mem_avail_kb)
    mem_pct = round(100.0 * used_kb / mem_total_kb, 2) if mem_total_kb else 0.0
    load = _read_loadavg()
    return {
        "source": "opspilot-agent",
        "loadavg_1m": float(load[0]) if load else 0.0,
        "memory_used_percent": mem_pct,
    }


def post_metrics(cfg: dict, metrics: dict) -> None:
    base = cfg["api_base_url"].rstrip("/")
    url = f"{base}/servers/{cfg['server_id']}/metrics"
    body = json.dumps(
        {
            "server_id": cfg["server_id"],
            "organization_id": cfg["organization_id"],
            "metrics": metrics,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": cfg["api_key"],
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        code = resp.getcode()
        if code not in (200, 201):
            raise RuntimeError(f"unexpected status {code}")


def main() -> None:
    interval = 60
    while True:
        try:
            cfg = load_config()
            interval = int(cfg.get("interval_seconds", 60))
            metrics = collect_metrics()
            post_metrics(cfg, metrics)
        except urllib.error.HTTPError as e:
            print(f"opspilot-agent: HTTP error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"opspilot-agent: error: {e}", file=sys.stderr)
        time.sleep(max(15, interval))


if __name__ == "__main__":
    main()

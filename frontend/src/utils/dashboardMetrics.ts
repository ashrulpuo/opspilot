/**
 * Maps GET /servers/{id}/metrics payloads (Salt push + legacy shapes) into Pinia Metric rows.
 */

/** Matches ``Metric`` in useSaltStream (avoids circular imports). */
export interface MetricRow {
  server_id: string
  metric_name: string
  metric_value: number
  unit: string
  timestamp: string
  metadata?: Record<string, unknown>
}

function isoNow(): string {
  return new Date().toISOString()
}

function num(v: unknown, fallback = 0): number {
  if (typeof v === 'number' && Number.isFinite(v)) {
    return v
  }
  if (typeof v === 'string' && v.trim() !== '') {
    const x = Number(v)
    return Number.isFinite(x) ? x : fallback
  }
  return fallback
}

/** Encode mount path for metric_name disk_usage_* (root → disk_usage__). */
export function diskMetricName(mountpoint: string): string {
  if (mountpoint === '/') {
    return 'disk_usage__'
  }
  const slug = mountpoint.replace(/^\//, '').replace(/\//g, '_')
  return `disk_usage_${slug}`
}

/** Reverse diskMetricName for display. */
export function mountpointFromDiskMetric(metricName: string): string {
  const raw = metricName.replace(/^disk_usage_/, '')
  if (raw === '_' || raw === '') {
    return '/'
  }
  return `/${raw.replace(/_/g, '/')}`
}

export function dashboardPayloadToMetrics(serverId: string, payload: Record<string, unknown>): MetricRow[] {
  if (!payload || typeof payload !== 'object') {
    return []
  }

  const ts = typeof payload.collected_at === 'string' ? payload.collected_at : isoNow()
  const schema = num(payload.schema_version, 0)

  const out: MetricRow[] = []

  const push = (name: string, value: number, unit: string, metadata?: Record<string, unknown>) => {
    out.push({
      server_id: serverId,
      metric_name: name,
      metric_value: value,
      unit,
      timestamp: ts,
      metadata,
    })
  }

  if (schema >= 2) {
    push('load_1min', num(payload.loadavg_1m), 'load')
    push('load_5min', num(payload.loadavg_5m), 'load')
    push('load_15min', num(payload.loadavg_15m), 'load')

    push('cpu_total_user', num(payload.cpu_total_user), '%')
    push('cpu_total_system', num(payload.cpu_total_system), '%')
    push('cpu_total_iowait', num(payload.cpu_total_iowait), '%')
    push('cpu_total_idle', num(payload.cpu_total_idle), '%')

    push('mem_total', num(payload.mem_total), 'bytes')
    push('mem_available', num(payload.mem_available), 'bytes')
    push('swap_total', num(payload.swap_total), 'bytes')
    push('swap_used', num(payload.swap_used), 'bytes')

    const mp = num(payload.memory_percent, NaN)
    if (!Number.isNaN(mp)) {
      push('memory_percent', mp, '%')
    }

    const cores = payload.cpu_cores
    if (Array.isArray(cores)) {
      cores.forEach((row, idx) => {
        if (!row || typeof row !== 'object') {
          return
        }
        const r = row as Record<string, unknown>
        const id = typeof r.name === 'string' ? r.name : String(idx)
        push(`cpu_${id}_user`, num(r.usage_percent), '%')
      })
    }

    const disks = payload.disks
    if (Array.isArray(disks)) {
      disks.forEach(d => {
        if (!d || typeof d !== 'object') {
          return
        }
        const row = d as Record<string, unknown>
        const mount = typeof row.mountpoint === 'string' ? row.mountpoint : '/'
        push(diskMetricName(mount), num(row.used_percent), '%', {
          used_bytes: num(row.used_bytes),
          total_bytes: num(row.total_bytes),
          fstype: typeof row.fstype === 'string' ? row.fstype : '',
          device: typeof row.device === 'string' ? row.device : '',
        })
      })
    }

    return out
  }

  // metrics_collector.get_system_metrics() shape (Salt pull / psutil)
  if (payload.hostname != null && typeof payload.cpu === 'object') {
    const cpu = payload.cpu as Record<string, unknown>
    const mp = num(cpu.percent)
    push('cpu_total_user', mp * 0.65, '%')
    push('cpu_total_system', mp * 0.25, '%')
    push('cpu_total_iowait', mp * 0.05, '%')
    push('cpu_total_idle', Math.max(0, 100 - mp), '%')
    push('cpu_0_user', mp, '%')

    const mem = payload.memory as Record<string, unknown> | undefined
    if (mem) {
      const pctMem = num(mem.percent)
      push('memory_percent', pctMem, '%')
      const totalGb = num(mem.total_gb)
      const usedGb = num(mem.used_gb)
      const totalBytes = totalGb * 1024 ** 3
      push('mem_total', totalBytes, 'bytes')
      push('mem_available', Math.max(0, totalBytes - usedGb * 1024 ** 3), 'bytes')
    }

    const load = payload.load_average as Record<string, unknown> | undefined
    if (load) {
      push('load_1min', num(load['1min']), 'load')
      push('load_5min', num(load['5min']), 'load')
      push('load_15min', num(load['15min']), 'load')
    }

    const diskObj = payload.disk as Record<string, Record<string, unknown>> | undefined
    if (diskObj && typeof diskObj === 'object') {
      for (const mountpoint of Object.keys(diskObj)) {
        const info = diskObj[mountpoint]
        if (!info) {
          continue
        }
        const usedGb = num(info.used_gb)
        const totalGb = num(info.total_gb)
        const usedBytes = usedGb * 1024 ** 3
        const totalBytes = totalGb * 1024 ** 3
        push(diskMetricName(mountpoint), num(info.percent), '%', {
          used_bytes: usedBytes,
          total_bytes: totalBytes,
          fstype: '',
          device: '',
        })
      }
    }

    return out
  }

  // Legacy minimal push-agent / old salt module
  push('load_1min', num(payload.loadavg_1m), 'load')
  push('load_5min', num(payload.loadavg_5m), 'load')
  push('load_15min', num(payload.loadavg_15m), 'load')

  const memPct = payload.memory_percent !== undefined ? payload.memory_percent : payload.memory_used_percent
  push('memory_percent', num(memPct), '%')

  const cpuPct = payload.cpu_percent !== undefined ? payload.cpu_percent : payload.cpu_usage
  if (cpuPct !== undefined) push('cpu_percent', num(cpuPct), '%')

  const diskPct = payload.disk_usage_percent !== undefined ? payload.disk_usage_percent : payload.disk_usage
  if (diskPct !== undefined) push('disk_usage_percent', num(diskPct), '%')

  // CPU breakdown + per-core fields from push agent
  for (const key of ['cpu_total_user', 'cpu_total_system', 'cpu_total_iowait', 'cpu_total_idle']) {
    if (payload[key] !== undefined) push(key, num(payload[key]), '%')
  }
  const coreRe = /^cpu_(\d+)_user$/
  for (const [key, val] of Object.entries(payload)) {
    if (coreRe.test(key) && val !== undefined) push(key, num(val), '%')
  }

  // Per-mount disk array from push agent
  const disksArr = payload.disks
  if (Array.isArray(disksArr)) {
    for (const d of disksArr) {
      if (!d || typeof d !== 'object') continue
      const row = d as Record<string, unknown>
      const mount = typeof row.mountpoint === 'string' ? row.mountpoint : '/'
      push(diskMetricName(mount), num(row.used_percent), '%', {
        used_bytes: num(row.used_bytes),
        total_bytes: num(row.total_bytes),
        fstype: typeof row.fstype === 'string' ? row.fstype : '',
        device: typeof row.device === 'string' ? row.device : '',
      })
    }
  }

  return out
}

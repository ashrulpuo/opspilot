<template>
  <div class="salt-metrics">

    <!-- ── Toolbar ──────────────────────────────────────────────── -->
    <div class="mbar">
      <div class="mbar-left">
        <span class="live-dot" :class="{ active: isConnected }"></span>
        <span class="live-label">{{ isConnected ? 'Live' : 'Offline' }}</span>
      </div>
      <div class="mbar-right">
        <el-button size="small" :icon="isAutoRefresh ? VideoPause : VideoPlay" @click="toggleAutoRefresh">
          {{ isAutoRefresh ? 'Pause' : 'Resume' }}
        </el-button>
        <el-button size="small" :icon="RefreshRight" :loading="refreshing" @click="refreshMetrics">
          Refresh
        </el-button>
        <el-dropdown trigger="click" @command="handleTimeRange">
          <el-button size="small">
            {{ timeRange.label }}<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="r in timeRanges" :key="r.value" :command="r.value">{{ r.label }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- ── KPI Row ───────────────────────────────────────────────── -->
    <div class="kpi-row">

      <!-- CPU -->
      <div class="kpi-chip" :style="{ '--kpi-accent': getCPUColor(overallCPU) }">
        <svg class="kpi-svg" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="48" fill="none" stroke="#e5e7eb" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="`${ARC_LEN.toFixed(2)} ${(ARC_CIRC - ARC_LEN).toFixed(2)}`"
            transform="rotate(135 60 60)" />
          <circle cx="60" cy="60" r="48" fill="none" :stroke="getCPUColor(overallCPU)" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="`${arcFill(overallCPU)} ${arcGap(overallCPU)}`"
            transform="rotate(135 60 60)" style="transition: stroke-dasharray 0.5s ease;" />
          <text x="60" y="68" text-anchor="middle" class="kpi-arc-text">{{ overallCPU.toFixed(0) }}%</text>
        </svg>
        <div class="kpi-meta">
          <div class="kpi-title">CPU</div>
          <div class="kpi-sub" :style="{ color: getCPUColor(overallCPU) }">{{ cpuStatusLabel }}</div>
        </div>
      </div>

      <!-- RAM -->
      <div class="kpi-chip" :style="{ '--kpi-accent': getMemoryColor(memPercent) }">
        <svg class="kpi-svg" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="48" fill="none" stroke="#e5e7eb" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="`${ARC_LEN.toFixed(2)} ${(ARC_CIRC - ARC_LEN).toFixed(2)}`"
            transform="rotate(135 60 60)" />
          <circle cx="60" cy="60" r="48" fill="none" :stroke="getMemoryColor(memPercent)" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="`${arcFill(memPercent)} ${arcGap(memPercent)}`"
            transform="rotate(135 60 60)" style="transition: stroke-dasharray 0.5s ease;" />
          <text x="60" y="68" text-anchor="middle" class="kpi-arc-text">{{ memPercent.toFixed(0) }}%</text>
        </svg>
        <div class="kpi-meta">
          <div class="kpi-title">RAM</div>
          <div class="kpi-sub">{{ formatMemory(memStats.used) }} / {{ formatMemory(memStats.total) }}</div>
        </div>
      </div>

      <!-- Disk -->
      <div class="kpi-chip" v-if="primaryDisk" :style="{ '--kpi-accent': getDiskColor(primaryDisk.used_percent) }">
        <svg class="kpi-svg" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="48" fill="none" stroke="#e5e7eb" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="`${ARC_LEN.toFixed(2)} ${(ARC_CIRC - ARC_LEN).toFixed(2)}`"
            transform="rotate(135 60 60)" />
          <circle cx="60" cy="60" r="48" fill="none" :stroke="getDiskColor(primaryDisk.used_percent)" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="`${arcFill(primaryDisk.used_percent)} ${arcGap(primaryDisk.used_percent)}`"
            transform="rotate(135 60 60)" style="transition: stroke-dasharray 0.5s ease;" />
          <text x="60" y="68" text-anchor="middle" class="kpi-arc-text">{{ primaryDisk.used_percent.toFixed(0) }}%</text>
        </svg>
        <div class="kpi-meta">
          <div class="kpi-title">Disk</div>
          <div class="kpi-sub">{{ primaryDisk.mountpoint }}</div>
        </div>
      </div>

      <!-- Load 1m -->
      <div class="kpi-chip kpi-load" :style="{ '--kpi-accent': getLoadRatioColor(loadRatio(loadAvg['1min'])) }">
        <div class="kpi-load-num" :style="{ color: getLoadRatioColor(loadRatio(loadAvg['1min'])) }">
          {{ loadAvgNull['1min'] != null ? loadAvg['1min'].toFixed(2) : '—' }}
        </div>
        <div class="kpi-load-ratio" :style="{ color: getLoadRatioColor(loadRatio(loadAvg['1min'])) }">
          {{ loadRatio(loadAvg['1min']).toFixed(2) }}× / core
        </div>
        <div class="kpi-load-footer">
          <span class="kpi-title">Load 1m</span>
          <span :class="['load-status', `load-status--${getLoadStatus(loadRatio(loadAvg['1min'])).toLowerCase().replace(' ', '-')}`]">
            {{ getLoadStatus(loadRatio(loadAvg['1min'])) }}
          </span>
        </div>
      </div>

    </div>

    <!-- ── Row 2: CPU | Memory ───────────────────────────────────── -->
    <div class="metrics-grid-2">

      <!-- CPU Card -->
      <el-card shadow="never" class="mcard">
        <template #header>
          <div class="mcard-hdr">
            <el-icon><Cpu /></el-icon><span>CPU Usage</span>
            <span class="mcard-time">{{ formatLastUpdate(lastCPUUpdate) }}</span>
          </div>
        </template>
        <div class="cpu-layout">
          <div class="cpu-gauge-col">
            <svg viewBox="0 0 120 120" class="big-gauge">
              <circle cx="60" cy="60" r="48" fill="none" stroke="#f3f4f6" stroke-width="12" stroke-linecap="round"
                :stroke-dasharray="`${ARC_LEN.toFixed(2)} ${(ARC_CIRC - ARC_LEN).toFixed(2)}`"
                transform="rotate(135 60 60)" />
              <circle cx="60" cy="60" r="48" fill="none" :stroke="getCPUColor(overallCPU)" stroke-width="12" stroke-linecap="round"
                :stroke-dasharray="`${arcFill(overallCPU)} ${arcGap(overallCPU)}`"
                transform="rotate(135 60 60)" style="transition: stroke-dasharray 0.5s ease;" />
              <text x="60" y="52" text-anchor="middle" class="gauge-pct" :fill="getCPUColor(overallCPU)">{{ overallCPU.toFixed(1) }}%</text>
              <text x="60" y="70" text-anchor="middle" class="gauge-sub-lbl">Overall</text>
            </svg>
            <div class="cpu-breakdown">
              <div class="cbd-row" v-for="s in cpuBreakdown" :key="s.label">
                <span class="cbd-lbl">{{ s.label }}</span>
                <div class="cbd-bar"><div class="cbd-fill" :style="{ width: Math.min(100, s.value) + '%', background: s.color }"></div></div>
                <span class="cbd-val">{{ s.value.toFixed(1) }}%</span>
              </div>
            </div>
          </div>
          <div class="cpu-cores-col">
            <div class="section-head">{{ cpuCores.length > 0 ? cpuCores.length + ' Cores' : 'Cores' }}</div>
            <el-scrollbar max-height="280px">
              <div class="htop-list" v-if="cpuCores.length > 0">
                <div class="htop-row" v-for="core in cpuCores" :key="core.core">
                  <span class="htop-lbl">{{ core.core }}</span>
                  <div class="htop-bar"><div class="htop-fill" :style="{ width: Math.min(100, core.value) + '%', background: getCPUColor(core.value) }"></div></div>
                  <span class="htop-val">{{ core.value.toFixed(0) }}%</span>
                </div>
              </div>
              <el-empty v-else description="Per-core data N/A" :image-size="48" />
            </el-scrollbar>
          </div>
        </div>
      </el-card>

      <!-- Memory Card -->
      <el-card shadow="never" class="mcard">
        <template #header>
          <div class="mcard-hdr">
            <el-icon><Memo /></el-icon><span>Memory</span>
            <span class="mcard-time">{{ formatLastUpdate(lastMemUpdate) }}</span>
          </div>
        </template>
        <div class="mem-layout">
          <div class="mem-gauge-col">
            <svg viewBox="0 0 120 120" class="big-gauge">
              <circle cx="60" cy="60" r="48" fill="none" stroke="#f3f4f6" stroke-width="12" stroke-linecap="round"
                :stroke-dasharray="`${ARC_LEN.toFixed(2)} ${(ARC_CIRC - ARC_LEN).toFixed(2)}`"
                transform="rotate(135 60 60)" />
              <circle cx="60" cy="60" r="48" fill="none" :stroke="getMemoryColor(memPercent)" stroke-width="12" stroke-linecap="round"
                :stroke-dasharray="`${arcFill(memPercent)} ${arcGap(memPercent)}`"
                transform="rotate(135 60 60)" style="transition: stroke-dasharray 0.5s ease;" />
              <text x="60" y="52" text-anchor="middle" class="gauge-pct" :fill="getMemoryColor(memPercent)">{{ memPercent.toFixed(1) }}%</text>
              <text x="60" y="70" text-anchor="middle" class="gauge-sub-lbl">Used</text>
            </svg>
          </div>
          <div class="mem-stats-col">
            <div class="mem-row" v-for="s in memRows" :key="s.label">
              <span class="mem-lbl">{{ s.label }}</span>
              <span class="mem-val" :style="s.color ? { color: s.color } : {}">{{ s.value }}</span>
            </div>
            <div class="seg-wrap">
              <div class="seg-bar">
                <div class="seg-used" :style="{ width: memPercent + '%', background: getMemoryColor(memPercent) }"></div>
              </div>
              <div class="seg-labels">
                <span :style="{ color: getMemoryColor(memPercent) }">Used {{ memPercent.toFixed(1) }}%</span>
                <span>Free {{ (100 - memPercent).toFixed(1) }}%</span>
              </div>
            </div>
            <template v-if="memStats.swap_total > 0">
              <div class="section-head" style="margin-top: 12px;">Swap</div>
              <div class="seg-bar" style="height: 6px;">
                <div class="seg-used" :style="{ width: swapPercent + '%', background: getMemoryColor(swapPercent) }"></div>
              </div>
              <div class="seg-labels">
                <span>{{ formatMemory(memStats.swap_used) }} / {{ formatMemory(memStats.swap_total) }}</span>
                <span>{{ swapPercent.toFixed(1) }}%</span>
              </div>
            </template>
          </div>
        </div>
      </el-card>

    </div>

    <!-- ── Row 3: Disk | Load ────────────────────────────────────── -->
    <div class="metrics-grid-2">

      <!-- Disk Card -->
      <el-card shadow="never" class="mcard">
        <template #header>
          <div class="mcard-hdr">
            <el-icon><Coin /></el-icon><span>Disk Volumes</span>
            <span class="mcard-time">{{ formatLastUpdate(lastDiskUpdate) }}</span>
          </div>
        </template>
        <div class="disk-list" v-if="diskUsage.length > 0">
          <div class="disk-mount" v-for="disk in diskUsage" :key="disk.mountpoint">
            <div class="disk-mhdr">
              <span class="disk-mp">{{ disk.mountpoint }}</span>
              <span class="disk-chip" :style="{ background: diskStatusStyle(disk.used_percent).bg, color: diskStatusStyle(disk.used_percent).fg }">
                {{ diskStatusStyle(disk.used_percent).label }}
              </span>
            </div>
            <div class="disk-bar">
              <div class="disk-fill" :style="{ width: Math.min(100, disk.used_percent) + '%', background: getDiskColor(disk.used_percent) }"></div>
            </div>
            <div class="disk-meta">
              <span>{{ disk.total > 0 ? `${formatBytes(disk.used)} / ${formatBytes(disk.total)}` : `${disk.used_percent.toFixed(1)}% used` }}</span>
              <span class="disk-fs">{{ [disk.fstype, disk.device].filter(Boolean).join(' · ') }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="No disk data" :image-size="60" />
      </el-card>

      <!-- Load Card -->
      <el-card shadow="never" class="mcard load-mcard">
        <template #header>
          <div class="mcard-hdr">
            <el-icon><TrendCharts /></el-icon><span>Load Average</span>
            <span class="load-cores-badge">{{ cpuCoreCount }} core{{ cpuCoreCount !== 1 ? 's' : '' }}</span>
            <span class="mcard-time">{{ formatLastUpdate(lastLoadUpdate) }}</span>
          </div>
        </template>
        <div class="load-body">
          <div class="load-col" v-for="p in loadPeriods" :key="p.key">
            <div class="load-period-lbl">{{ p.label }}</div>
            <svg v-if="loadHistory[p.key].length > 1" class="load-spark" viewBox="0 0 100 40" preserveAspectRatio="none">
              <polyline :points="sparklinePoints(loadHistory[p.key])" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <div v-else class="load-spark"></div>
            <div class="load-big" :style="{ color: getLoadRatioColor(loadRatio(loadAvg[p.key])) }">
              {{ loadAvgNull[p.key] != null ? loadAvg[p.key].toFixed(2) : '—' }}
            </div>
            <div class="load-ratio-lbl" :style="{ color: getLoadRatioColor(loadRatio(loadAvg[p.key])) }">
              {{ loadRatio(loadAvg[p.key]).toFixed(2) }}× / core
            </div>
            <div class="load-ratio-bar">
              <div class="load-ratio-fill" :style="{ width: Math.min(100, loadRatio(loadAvg[p.key]) / 3 * 100) + '%', background: getLoadRatioColor(loadRatio(loadAvg[p.key])) }"></div>
            </div>
            <span :class="['load-status', `load-status--${getLoadStatus(loadRatio(loadAvg[p.key])).toLowerCase().replace(' ', '-')}`]">
              {{ getLoadStatus(loadRatio(loadAvg[p.key])) }}
            </span>
          </div>
        </div>
        <div class="load-legend">
          <span class="load-status load-status--comfortable">Comfortable</span><span class="load-legend-range">&lt;0.7×</span>
          <span class="load-status load-status--getting-busy">Getting Busy</span><span class="load-legend-range">0.7–1×</span>
          <span class="load-status load-status--saturated">Saturated</span><span class="load-legend-range">1–2×</span>
          <span class="load-status load-status--overloaded">Overloaded</span><span class="load-legend-range">&gt;2×</span>
        </div>
      </el-card>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, watch, onUnmounted, computed } from 'vue'
import { RefreshRight, Cpu, Memo, Coin, TrendCharts, VideoPause, VideoPlay, ArrowDown } from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'
import { mountpointFromDiskMetric } from '@/utils/dashboardMetrics'
import { useServerStore } from '@/stores/server'

const props = defineProps<{
  serverId: string
}>()

const { metrics, isConnected, hydrateDashboardMetrics } = useSaltStream(props.serverId)
const serverStore = useServerStore()

const timeRanges = [
  { label: '1 Hour', value: '1h' },
  { label: '6 Hours', value: '6h' },
  { label: '24 Hours', value: '24h' },
  { label: '7 Days', value: '7d' },
  { label: '30 Days', value: '30d' },
]
const timeRange = ref(timeRanges[0])
const isAutoRefresh = ref(true)
const refreshing = ref(false)
let refreshInterval: any = null

const mNull = (...names: string[]): number | null => {
  for (const name of names) {
    const v = metrics.value[name]?.metric_value
    if (v != null && Number.isFinite(v)) return v
  }
  return null
}

const m = (...names: string[]): number => mNull(...names) ?? 0
const mTs = (...names: string[]): string | null => {
  for (const name of names) {
    const ts = metrics.value[name]?.timestamp
    if (ts) return ts
  }
  return null
}

// ── CPU ──────────────────────────────────────────────────────────────────────

const overallCPU = computed(() =>
  Math.min(100, m('cpu_percent', 'cpu_usage', 'cpu_total_user', 'cpu_0_user'))
)

const cpuCores = computed(() => {
  const out: { core: string; value: number }[] = []
  for (const metric of Object.values(metrics.value)) {
    const name = metric.metric_name
    if (name?.startsWith('cpu_') && name.endsWith('_user') && !name.startsWith('cpu_total')) {
      out.push({ core: name.split('_')[1], value: metric.metric_value ?? 0 })
    }
  }
  return out
})

const cpuStats = computed(() => ({
  user:   m('cpu_total_user'),
  system: m('cpu_total_system'),
  iowait: m('cpu_total_iowait'),
  idle:   m('cpu_total_idle'),
}))

// ── Memory ───────────────────────────────────────────────────────────────────

const serverMemoryMb = computed(() => {
  const s = serverStore.servers[props.serverId] as any
  return Number(s?.memory_mb ?? s?.agent_memory_mb ?? 0)
})

const memPercentRaw = computed(() =>
  Math.min(100, m('memory_percent', 'memory_used_percent'))
)

const memStats = computed(() => {
  const totalBytes = m('mem_total')
  const availBytes = m('mem_available')
  if (totalBytes > 0) {
    return { total: totalBytes, available: availBytes, used: Math.max(0, totalBytes - availBytes), swap_total: m('swap_total'), swap_used: m('swap_used') }
  }
  const totalFromProfile = serverMemoryMb.value * 1024 * 1024
  const pct = memPercentRaw.value / 100
  return {
    total: totalFromProfile,
    available: totalFromProfile > 0 ? Math.max(0, totalFromProfile * (1 - pct)) : 0,
    used: totalFromProfile > 0 ? totalFromProfile * pct : 0,
    swap_total: 0,
    swap_used: 0,
  }
})

const memPercent = computed(() => {
  const { total, available } = memStats.value
  if (total > 0) return Math.min(100, ((total - available) / total) * 100)
  return memPercentRaw.value
})

const swapPercent = computed(() => {
  const { swap_total, swap_used } = memStats.value
  return swap_total > 0 ? Math.min(100, (swap_used / swap_total) * 100) : 0
})

// ── Disk ─────────────────────────────────────────────────────────────────────

const diskUsage = computed(() => {
  const disks: any[] = []
  for (const metric of Object.values(metrics.value)) {
    const name = metric.metric_name
    if (!name?.startsWith('disk_usage_')) continue
    if (name === 'disk_usage_percent' || name === 'disk_usage') continue
    const mountpoint = mountpointFromDiskMetric(name)
    const meta = (metric.metadata ?? {}) as Record<string, unknown>
    const used = typeof meta.used_bytes === 'number' ? meta.used_bytes : typeof meta.used_gb === 'number' ? meta.used_gb * 1024 ** 3 : 0
    const total = typeof meta.total_bytes === 'number' ? meta.total_bytes : typeof meta.total_gb === 'number' ? meta.total_gb * 1024 ** 3 : 0
    disks.push({ mountpoint, used, total, used_percent: metric.metric_value ?? 0, fstype: typeof meta.fstype === 'string' ? meta.fstype : '', device: typeof meta.device === 'string' ? meta.device : '' })
  }
  if (disks.length === 0) {
    const d = metrics.value['disk_usage_percent'] ?? metrics.value['disk_usage']
    if (d) disks.push({ mountpoint: '/', used: 0, total: 0, used_percent: Math.min(100, d.metric_value ?? 0), fstype: '', device: '' })
  }
  return disks
})

// ── Load ─────────────────────────────────────────────────────────────────────

const loadAvg = computed(() => ({
  '1min':  m('loadavg_1m',  'load_1min'),
  '5min':  m('loadavg_5m',  'load_5min'),
  '15min': m('loadavg_15m', 'load_15min'),
}))

const cpuCoreCount = computed(() => {
  const s = serverStore.servers[props.serverId] as any
  const fromProfile = Number(s?.cpu_cores ?? s?.agent_cpu_cores ?? 0)
  return fromProfile > 0 ? fromProfile : (cpuCores.value.length || 1)
})

const loadRatio = (val: number): number =>
  cpuCoreCount.value > 0 ? val / cpuCoreCount.value : 0

const getLoadRatioColor = (ratio: number): string =>
  ratio < 0.7 ? '#67C23A' : ratio < 1.0 ? '#E6A23C' : ratio < 2.0 ? '#F59E0B' : '#F56C6C'

const getLoadStatus = (ratio: number): string =>
  ratio < 0.7 ? 'Comfortable' : ratio < 1.0 ? 'Getting Busy' : ratio < 2.0 ? 'Saturated' : 'Overloaded'

const MAX_LOAD_HISTORY = 30
const _loadBuf: Record<string, number[]> = { '1min': [], '5min': [], '15min': [] }
const loadHistory = shallowRef<Record<string, number[]>>({ '1min': [], '5min': [], '15min': [] })

watch(loadAvg, (val) => {
  for (const key of ['1min', '5min', '15min'] as const) {
    _loadBuf[key].push(val[key])
    if (_loadBuf[key].length > MAX_LOAD_HISTORY) _loadBuf[key].shift()
  }
  loadHistory.value = { '1min': [..._loadBuf['1min']], '5min': [..._loadBuf['5min']], '15min': [..._loadBuf['15min']] }
}, { immediate: true })

const sparklinePoints = (data: number[]): string => {
  if (data.length < 2) return ''
  const W = 100, H = 40
  const max = Math.max(...data, 0.01)
  return data.map((v, i) => {
    const x = (i / (data.length - 1)) * W
    const y = H - (v / max) * (H - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

// ── Timestamps ───────────────────────────────────────────────────────────────

const lastCPUUpdate  = computed(() => mTs('cpu_percent', 'cpu_usage', 'cpu_0_user'))
const lastMemUpdate  = computed(() => mTs('memory_percent', 'memory_used_percent', 'mem_total'))
const lastDiskUpdate = computed(() => mTs('disk_usage_percent', 'disk_usage', 'disk_usage__'))
const lastLoadUpdate = computed(() => mTs('loadavg_1m', 'load_1min'))

// ── Helpers ──────────────────────────────────────────────────────────────────

const formatMemory = (bytes: number | undefined) => {
  if (!bytes || bytes === 0) return '-'
  const gb = bytes / 1024 ** 3
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  const mb = bytes / 1024 ** 2
  if (mb >= 1) return `${mb.toFixed(0)} MB`
  return `${bytes} B`
}

const formatBytes = (bytes: number | undefined) => {
  if (!bytes || bytes === 0) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes, i = 0
  while (value >= 1024 && i < units.length - 1) { value /= 1024; i++ }
  return `${value.toFixed(1)} ${units[i]}`
}

const formatLastUpdate = (ts: string | null) => {
  if (!ts) return '-'
  const diff = Date.now() - new Date(ts).getTime()
  if (diff < 60000) return 'Just now'
  if (diff < 120000) return '1m ago'
  if (diff < 300000) return '5m ago'
  return '>5m ago'
}

const getCPUColor    = (v: number) => v < 50 ? '#67C23A' : v < 70 ? '#E6A23C' : v < 85 ? '#F59E0B' : '#F56C6C'
const getMemoryColor = (v: number) => v < 50 ? '#67C23A' : v < 70 ? '#E6A23C' : v < 85 ? '#F59E0B' : '#F56C6C'
const getDiskColor   = (v: number) => v < 70 ? '#67C23A' : v < 85 ? '#E6A23C' : v < 90 ? '#F59E0B' : '#F56C6C'

// ── Actions ───────────────────────────────────────────────────────────────────

const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value
  if (!isAutoRefresh.value && refreshInterval) { clearInterval(refreshInterval); refreshInterval = null }
}

const refreshMetrics = async () => {
  refreshing.value = true
  try { await hydrateDashboardMetrics() } catch { /* silent */ } finally { refreshing.value = false }
}

const handleTimeRange = (range: string) => {
  const selected = timeRanges.find(r => r.value === range)
  if (selected) timeRange.value = selected
}

onUnmounted(() => { if (refreshInterval) clearInterval(refreshInterval) })

// ── Arc gauge math ────────────────────────────────────────────────────────────

const ARC_R    = 48
const ARC_CIRC = 2 * Math.PI * ARC_R   // 301.59
const ARC_LEN  = ARC_CIRC * 0.75       // 226.19 — 270° arc

const arcFill = (pct: number): string =>
  (Math.min(Math.max(pct, 0), 100) / 100 * ARC_LEN).toFixed(2)

const arcGap = (pct: number): string =>
  (ARC_CIRC - Math.min(Math.max(pct, 0), 100) / 100 * ARC_LEN).toFixed(2)

// ── New computed helpers ──────────────────────────────────────────────────────

const cpuBreakdown = computed(() => [
  { label: 'User', value: cpuStats.value.user,   color: '#3b82f6' },
  { label: 'Sys',  value: cpuStats.value.system, color: '#8b5cf6' },
  { label: 'I/O',  value: cpuStats.value.iowait, color: '#f59e0b' },
  { label: 'Idle', value: cpuStats.value.idle,   color: '#10b981' },
])

const cpuStatusLabel = computed(() => {
  const v = overallCPU.value
  if (v < 50) return 'Normal'
  if (v < 70) return 'Moderate'
  if (v < 85) return 'High'
  return 'Critical'
})

const primaryDisk = computed(() => {
  if (diskUsage.value.length === 0) return null
  return diskUsage.value.find(d => d.mountpoint === '/') ?? diskUsage.value[0]
})

const diskStatusStyle = (pct: number) => {
  if (pct < 60) return { label: 'OK',   bg: '#d1fae5', fg: '#065f46' }
  if (pct < 80) return { label: 'WARN', bg: '#fef3c7', fg: '#92400e' }
  if (pct < 90) return { label: 'HIGH', bg: '#ffedd5', fg: '#9a3412' }
  return              { label: 'CRIT', bg: '#fee2e2', fg: '#991b1b' }
}

const memRows = computed(() => [
  { label: 'Total',     value: formatMemory(memStats.value.total) },
  { label: 'Used',      value: formatMemory(memStats.value.used),      color: getMemoryColor(memPercent.value) },
  { label: 'Available', value: formatMemory(memStats.value.available) },
])

const loadPeriods: Array<{ key: '1min' | '5min' | '15min'; label: string }> = [
  { key: '1min',  label: '1 Min'  },
  { key: '5min',  label: '5 Min'  },
  { key: '15min', label: '15 Min' },
]

const loadAvgNull = computed<Record<'1min' | '5min' | '15min', number | null>>(() => ({
  '1min':  mNull('loadavg_1m',  'load_1min'),
  '5min':  mNull('loadavg_5m',  'load_5min'),
  '15min': mNull('loadavg_15m', 'load_15min'),
}))
</script>

<style scoped>
/* ── Root ──────────────────────────────────────────────────────── */
.salt-metrics {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Toolbar ───────────────────────────────────────────────────── */
.mbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
}

.mbar-left {
  display: flex;
  align-items: center;
  gap: 7px;
}

.mbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  flex-shrink: 0;
  transition: background 0.3s;
}

.live-dot.active {
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
  animation: pulse-live 2s infinite;
}

@keyframes pulse-live {
  0%, 100% { box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2); }
  50%       { box-shadow: 0 0 0 7px rgba(16, 185, 129, 0.04); }
}

.live-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

/* ── KPI Row ───────────────────────────────────────────────────── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.kpi-chip {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-top: 3px solid var(--kpi-accent, #409eff);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: box-shadow 0.2s;
}

.kpi-chip:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.07);
}

.kpi-svg {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
}

.kpi-arc-text {
  font-size: 24px;
  font-weight: 700;
  fill: #111827;
}

.kpi-meta {
  flex: 1;
  min-width: 0;
}

.kpi-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.kpi-sub {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Load KPI — column layout, no arc */
.kpi-load {
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.kpi-load-num {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.kpi-load-ratio {
  font-size: 11px;
  font-weight: 600;
}

.kpi-load-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  flex-wrap: wrap;
}

/* ── 2-col grid ────────────────────────────────────────────────── */
.metrics-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* ── Card common ───────────────────────────────────────────────── */
.mcard-hdr {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.mcard-time {
  margin-left: auto;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-weight: 400;
}

.section-head {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
}

/* ── Big gauge SVG ─────────────────────────────────────────────── */
.big-gauge {
  width: 140px;
  height: 140px;
  display: block;
}

.gauge-pct {
  font-size: 20px;
  font-weight: 700;
}

.gauge-sub-lbl {
  font-size: 11px;
  fill: #9ca3af;
  font-weight: 500;
}

/* ── CPU Layout ────────────────────────────────────────────────── */
.cpu-layout {
  display: flex;
  gap: 20px;
  min-height: 260px;
}

.cpu-gauge-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 0 160px;
}

.cpu-breakdown {
  width: 100%;
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.cbd-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cbd-lbl {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  width: 28px;
  text-align: right;
  flex-shrink: 0;
}

.cbd-bar {
  flex: 1;
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.cbd-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.cbd-val {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.cpu-cores-col {
  flex: 1;
  min-width: 0;
  border-left: 1px solid var(--el-border-color-lighter);
  padding-left: 16px;
}

.htop-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.htop-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.htop-lbl {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--el-text-color-secondary);
  width: 30px;
  text-align: right;
  flex-shrink: 0;
}

.htop-bar {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.htop-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.htop-val {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  width: 30px;
  text-align: right;
  flex-shrink: 0;
}

/* ── Memory Layout ─────────────────────────────────────────────── */
.mem-layout {
  display: flex;
  gap: 20px;
  min-height: 260px;
}

.mem-gauge-col {
  flex: 0 0 160px;
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.mem-stats-col {
  flex: 1;
  min-width: 0;
  border-left: 1px solid var(--el-border-color-lighter);
  padding-left: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mem-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.mem-lbl { color: var(--el-text-color-secondary); }
.mem-val { font-weight: 600; color: var(--el-text-color-primary); }

.seg-wrap { margin-top: 4px; }

.seg-bar {
  height: 10px;
  background: #f3f4f6;
  border-radius: 5px;
  overflow: hidden;
}

.seg-used {
  height: 100%;
  border-radius: 5px;
  transition: width 0.4s ease;
}

.seg-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

/* ── Disk ──────────────────────────────────────────────────────── */
.disk-list {
  display: flex;
  flex-direction: column;
}

.disk-mount {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.disk-mount:last-child { border-bottom: none; }

.disk-mhdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.disk-mp {
  font-size: 14px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  color: var(--el-text-color-primary);
}

.disk-chip {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 10px;
}

.disk-bar {
  height: 10px;
  background: #f3f4f6;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 6px;
}

.disk-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.4s ease;
}

.disk-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.disk-fs {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

/* ── Load Card ─────────────────────────────────────────────────── */
.load-mcard {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.load-mcard :deep(.el-card__header) {
  background: transparent;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.load-mcard :deep(.el-card__body) {
  background: transparent;
}

.load-mcard .mcard-hdr {
  color: white;
}

.load-mcard .mcard-time {
  color: rgba(255, 255, 255, 0.55);
}

.load-cores-badge {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.85);
  border-radius: 10px;
  padding: 2px 8px;
  font-weight: 500;
}

.load-body {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 4px 0 8px;
}

.load-col {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.load-period-lbl {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.65);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.load-spark {
  display: block;
  width: 100%;
  height: 36px;
}

.load-big {
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
}

.load-ratio-lbl {
  font-size: 11px;
  font-weight: 600;
}

.load-ratio-bar {
  width: 80%;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  overflow: hidden;
  margin: 2px 0;
}

.load-ratio-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}

/* Load status badges */
.load-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #fff;
}

.load-status--comfortable  { background: #22c55e; }
.load-status--getting-busy { background: #f59e0b; }
.load-status--saturated    { background: #f97316; }
.load-status--overloaded   { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }

.load-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.load-legend-range {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  margin-right: 6px;
}
</style>

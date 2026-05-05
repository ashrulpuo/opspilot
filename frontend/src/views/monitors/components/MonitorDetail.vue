<template>
  <el-drawer
    v-model="visible"
    :title="monitor?.name ?? 'Monitor Details'"
    size="560px"
    :destroy-on-close="true"
    class="monitor-drawer"
  >
    <template v-if="monitor">
      <!-- Status header -->
      <div class="detail-header">
        <div class="detail-status-row">
          <span :class="['detail-dot', `dot-${currentStatus}`]">
            <span v-if="currentStatus === 'down'" class="pulse-ring" />
          </span>
          <span :class="['detail-status-label', `label-${currentStatus}`]">{{ statusLabel }}</span>
          <el-tag :type="typeTagType" size="small" effect="plain" style="margin-left: auto">
            {{ monitor.type.toUpperCase() }}
          </el-tag>
        </div>
        <p class="detail-url">{{ monitor.url }}</p>

        <div class="detail-stats">
          <div class="stat">
            <span class="stat-label">Avg Response</span>
            <span class="stat-value">{{ monitor.avg_response_time_ms != null ? `${Math.round(monitor.avg_response_time_ms)}ms` : '—' }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Uptime 30d</span>
            <span class="stat-value" :style="{ color: uptimeColor }">
              {{ monitor.uptime_30d != null ? `${monitor.uptime_30d.toFixed(2)}%` : '—' }}
            </span>
          </div>
          <div v-if="monitor.ssl_days_remaining != null" class="stat">
            <span class="stat-label">SSL Expiry</span>
            <span class="stat-value" :style="{ color: sslColor }">{{ monitor.ssl_days_remaining }}d</span>
          </div>
          <div class="stat">
            <span class="stat-label">Interval</span>
            <span class="stat-value">{{ intervalLabel }}</span>
          </div>
        </div>
      </div>

      <el-divider />

      <!-- Response time chart -->
      <div class="section-title">Response Time (24h)</div>
      <div v-if="checksLoading" class="chart-placeholder">
        <el-skeleton :rows="4" animated />
      </div>
      <div v-else-if="chartData.length" ref="chartEl" class="response-chart" />
      <el-empty v-else description="No check data yet" :image-size="60" />

      <el-divider />

      <!-- Incident history -->
      <div class="section-title">
        Incident History
        <el-tag v-if="openIncident" type="danger" size="small" effect="light" style="margin-left: 8px">Active</el-tag>
      </div>
      <div v-if="incidentsLoading">
        <el-skeleton :rows="3" animated />
      </div>
      <el-empty v-else-if="!incidents.length" description="No incidents" :image-size="60" />
      <div v-else class="incident-list">
        <div
          v-for="inc in incidents"
          :key="inc.id"
          :class="['incident-row', { 'is-open': !inc.resolved_at }]"
        >
          <div class="incident-body">
            <div class="incident-time">
              <el-icon><Timer /></el-icon>
              {{ formatDate(inc.started_at) }}
              <span v-if="inc.resolved_at" class="incident-resolved">
                → {{ formatDate(inc.resolved_at) }}
              </span>
            </div>
            <div class="incident-duration">
              <span v-if="inc.duration_seconds != null">
                Duration: {{ formatDuration(inc.duration_seconds) }}
              </span>
              <el-tag v-else type="danger" size="small" effect="plain">Ongoing</el-tag>
            </div>
          </div>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Timer } from '@element-plus/icons-vue'
import type { Monitor, MonitorCheck, MonitorIncident } from '@/api/opspilot/monitors'
import { MonitorsAPI } from '@/api/opspilot/monitors'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  modelValue: boolean
  monitor: Monitor | null
}>()

const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const recentChecks = ref<MonitorCheck[]>([])
const incidents = ref<MonitorIncident[]>([])
const checksLoading = ref(false)
const incidentsLoading = ref(false)
const chartEl = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const currentStatus = computed(() => {
  if (!props.monitor?.enabled) return 'paused'
  return props.monitor?.last_status ?? 'pending'
})

const statusLabel = computed(() => ({
  up: 'Operational', down: 'Down', pending: 'Checking…', paused: 'Paused',
}[currentStatus.value] ?? '—'))

const uptimeColor = computed(() => {
  const v = props.monitor?.uptime_30d ?? 100
  return v >= 99 ? '#67c23a' : v >= 95 ? '#e6a23c' : '#f56c6c'
})

const sslColor = computed(() => {
  const d = props.monitor?.ssl_days_remaining ?? 999
  return d <= 7 ? '#f56c6c' : d <= 30 ? '#e6a23c' : '#67c23a'
})

const typeTagType = computed(() =>
  ({ http: 'info', https: 'success', tcp: 'warning', dns: '', push: 'danger' }[props.monitor?.type ?? ''] ?? '') as any
)

const intervalLabel = computed(() => {
  const s = props.monitor?.interval_seconds ?? 300
  if (s < 60) return `${s}s`
  if (s < 3600) return `${s / 60}m`
  return `${s / 3600}h`
})

const openIncident = computed(() => incidents.value.find(i => !i.resolved_at))

const chartData = computed(() =>
  recentChecks.value
    .filter(c => c.response_time_ms != null)
    .map(c => [new Date(c.checked_at).getTime(), c.response_time_ms as number])
)

watch([() => props.modelValue, () => props.monitor?.id], async ([open]) => {
  if (!open || !props.monitor) return
  await Promise.all([loadChecks(), loadIncidents()])
})

async function loadChecks() {
  if (!props.monitor) return
  checksLoading.value = true
  try {
    recentChecks.value = await MonitorsAPI.getChecks(props.monitor.id, 24)
    await nextTick()
    renderChart()
  } finally {
    checksLoading.value = false
  }
}

async function loadIncidents() {
  if (!props.monitor) return
  incidentsLoading.value = true
  try {
    incidents.value = await MonitorsAPI.getIncidents(props.monitor.id)
  } finally {
    incidentsLoading.value = false
  }
}

function renderChart() {
  if (!chartEl.value || !chartData.value.length) return
  chart?.dispose()
  chart = echarts.init(chartEl.value)
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        return `${new Date(p.value[0]).toLocaleTimeString()}<br/><b>${p.value[1]}ms</b>`
      },
    },
    grid: { top: 8, right: 8, bottom: 28, left: 52 },
    xAxis: {
      type: 'time',
      axisLabel: { fontSize: 11, color: '#909399' },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'ms',
      nameTextStyle: { fontSize: 11, color: '#909399' },
      axisLabel: { fontSize: 11, color: '#909399' },
      splitLine: { lineStyle: { color: 'rgba(144,147,153,0.15)' } },
    },
    series: [{
      type: 'line',
      data: chartData.value,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#409eff', width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64,158,255,0.25)' },
            { offset: 1, color: 'rgba(64,158,255,0)' },
          ],
        },
      },
    }],
  })
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

function formatDuration(s: number) {
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
}
</script>

<style scoped>
.detail-header {
  padding: 4px 0 8px;
}

.detail-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.detail-dot {
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #909399;
  position: relative;
  flex-shrink: 0;

  &.dot-up      { background: #67c23a; }
  &.dot-down    { background: #f56c6c; }
  &.dot-pending { background: #e6a23c; }
}

.pulse-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid #f56c6c;
  animation: pulse 1.6s ease-out infinite;
}

@keyframes pulse {
  0%   { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(2.2); opacity: 0; }
}

.detail-status-label {
  font-size: 13px;
  font-weight: 600;
  &.label-up      { color: #67c23a; }
  &.label-down    { color: #f56c6c; }
  &.label-pending { color: #e6a23c; }
  &.label-paused  { color: #909399; }
}

.detail-url {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: 'SFMono-Regular', Consolas, monospace;
  margin: 0 0 16px;
  word-break: break-all;
}

.detail-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--el-text-color-placeholder);
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
}

.response-chart {
  width: 100%;
  height: 180px;
}

.chart-placeholder {
  height: 180px;
}

.incident-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.incident-row {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border-left: 3px solid var(--el-border-color);

  &.is-open {
    border-left-color: #f56c6c;
    background: rgba(245, 108, 108, 0.06);
  }
}

.incident-body {
  flex: 1;
  min-width: 0;
}

.incident-time {
  font-size: 12px;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.incident-resolved {
  color: var(--el-text-color-secondary);
}

.incident-duration {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
</style>

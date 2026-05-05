<template>
  <div
    :class="['monitor-card', `status-${status}`, { 'is-paused': !monitor.enabled }]"
    @click="$emit('click', monitor)"
  >
    <!-- Left accent bar via ::before in CSS -->

    <!-- Header -->
    <div class="card-header">
      <div class="status-indicator">
        <span :class="['status-dot', `dot-${status}`]">
          <span v-if="status === 'down'" class="pulse-ring" />
        </span>
      </div>
      <div class="monitor-meta">
        <p class="monitor-name">{{ monitor.name }}</p>
        <p class="monitor-url">{{ displayUrl }}</p>
      </div>
      <div class="card-actions" @click.stop>
        <el-dropdown trigger="click" @command="handleCommand">
          <el-icon class="action-btn"><MoreFilled /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">Edit</el-dropdown-item>
              <el-dropdown-item :command="monitor.enabled ? 'pause' : 'resume'">
                {{ monitor.enabled ? 'Pause' : 'Resume' }}
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided style="color: var(--el-color-danger)">
                Delete
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- Metrics row -->
    <div class="metrics-row">
      <div class="metric">
        <span class="metric-label">Response</span>
        <span class="metric-value">
          {{ monitor.avg_response_time_ms != null ? `${Math.round(monitor.avg_response_time_ms)}ms` : '—' }}
        </span>
      </div>
      <div class="metric">
        <span class="metric-label">Uptime 30d</span>
        <span class="metric-value" :style="{ color: uptimeColor }">
          {{ monitor.uptime_30d != null ? `${monitor.uptime_30d.toFixed(2)}%` : '—' }}
        </span>
      </div>
      <div v-if="monitor.ssl_days_remaining != null" class="metric">
        <span class="metric-label">SSL</span>
        <span class="metric-value" :style="{ color: sslColor }">
          {{ monitor.ssl_days_remaining }}d
        </span>
      </div>
      <div class="metric type-badge-wrap">
        <el-tag :type="typeTagType" size="small" effect="plain" class="type-tag">
          {{ monitor.type.toUpperCase() }}
        </el-tag>
      </div>
    </div>

    <!-- 30-bar uptime history strip -->
    <div class="uptime-strip">
      <div
        v-for="(bar, i) in uptimeBars"
        :key="i"
        :class="['uptime-bar', `bar-${bar.status}`]"
        :title="bar.label"
      />
    </div>

    <!-- Footer -->
    <div class="card-footer">
      <span class="last-checked">
        <el-icon><Clock /></el-icon>
        {{ lastCheckedLabel }}
      </span>
      <span :class="['status-label', `label-${status}`]">{{ statusLabel }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MoreFilled, Clock } from '@element-plus/icons-vue'
import type { Monitor, MonitorCheck } from '@/api/opspilot/monitors'

const props = defineProps<{
  monitor: Monitor
  recentChecks?: MonitorCheck[]
}>()

const emit = defineEmits<{
  click: [monitor: Monitor]
  edit: [monitor: Monitor]
  pause: [monitor: Monitor]
  resume: [monitor: Monitor]
  delete: [monitor: Monitor]
}>()

const status = computed(() => {
  if (!props.monitor.enabled) return 'paused'
  return props.monitor.last_status ?? 'pending'
})

const statusLabel = computed(() => ({
  up: 'Operational', down: 'Down', pending: 'Checking…', paused: 'Paused',
}[status.value] ?? '—'))

const displayUrl = computed(() => {
  try {
    const u = new URL(props.monitor.url)
    return u.hostname + (u.pathname !== '/' ? u.pathname : '')
  } catch { return props.monitor.url }
})

const uptimeColor = computed(() => {
  const v = props.monitor.uptime_30d ?? 100
  return v >= 99 ? '#67c23a' : v >= 95 ? '#e6a23c' : '#f56c6c'
})

const sslColor = computed(() => {
  const d = props.monitor.ssl_days_remaining ?? 999
  return d <= 7 ? '#f56c6c' : d <= 30 ? '#e6a23c' : '#67c23a'
})

const typeTagType = computed(() =>
  ({ http: 'info', https: 'success', tcp: 'warning', dns: '', push: 'danger' }[props.monitor.type] ?? '') as any
)

const uptimeBars = computed(() => {
  const checks = props.recentChecks
  if (checks?.length) {
    return checks.slice(-30).map(c => ({
      status: c.status,
      label: `${new Date(c.checked_at).toLocaleString()} — ${c.status}`,
    }))
  }
  return Array.from({ length: 30 }, (_, i) => ({
    status: i < 29 ? 'up' : (props.monitor.last_status ?? 'pending'),
    label: '',
  }))
})

const lastCheckedLabel = computed(() => {
  if (!props.monitor.last_checked_at) return 'Never'
  const diff = Date.now() - new Date(props.monitor.last_checked_at).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  return hrs < 24 ? `${hrs}h ago` : `${Math.floor(hrs / 24)}d ago`
})

function handleCommand(cmd: string) {
  if (cmd === 'edit') emit('edit', props.monitor)
  else if (cmd === 'pause') emit('pause', props.monitor)
  else if (cmd === 'resume') emit('resume', props.monitor)
  else if (cmd === 'delete') emit('delete', props.monitor)
}
</script>

<style scoped>
.monitor-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 20px 20px 16px 24px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    border-radius: 12px 0 0 12px;
    background: var(--el-border-color);
    transition: background 0.2s;
  }
  &.status-up::before    { background: #67c23a; }
  &.status-down::before  { background: #f56c6c; }
  &.status-pending::before { background: #e6a23c; }

  &:hover {
    border-color: var(--el-color-primary-light-5);
    box-shadow: 0 6px 24px rgba(0,0,0,0.09);
    transform: translateY(-2px);
  }
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 14px;
}

.status-indicator {
  flex-shrink: 0;
  margin-top: 3px;
  position: relative;
  width: 12px; height: 12px;
}

.status-dot {
  display: block;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #909399;
  position: relative;
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

.monitor-meta { flex: 1; min-width: 0; }

.monitor-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 2px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.monitor-url {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-family: 'SFMono-Regular', Consolas, monospace;
}

.action-btn {
  color: var(--el-text-color-placeholder);
  cursor: pointer; font-size: 16px;
  padding: 4px; border-radius: 4px;
  transition: all 0.15s;
  &:hover { color: var(--el-text-color-primary); background: var(--el-fill-color-light); }
}

.metrics-row {
  display: flex; align-items: center; gap: 18px; margin-bottom: 12px;
}

.metric { display: flex; flex-direction: column; gap: 1px; }

.metric-label {
  font-size: 10px; font-weight: 500;
  color: var(--el-text-color-placeholder);
  text-transform: uppercase; letter-spacing: 0.04em;
}

.metric-value {
  font-size: 13px; font-weight: 600;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}

.type-badge-wrap { margin-left: auto; }

.type-tag { font-size: 10px; font-weight: 600; letter-spacing: 0.04em; }

.uptime-strip {
  display: flex; gap: 2px; height: 26px;
  align-items: stretch; margin-bottom: 12px;
}

.uptime-bar {
  flex: 1; border-radius: 2px;
  background: var(--el-border-color-lighter);
  transition: filter 0.1s;
  cursor: default;
  &:hover { filter: brightness(1.15); }
  &.bar-up      { background: #67c23a; }
  &.bar-down    { background: #f56c6c; }
  &.bar-pending { background: #e6a23c; }
}

.card-footer {
  display: flex; justify-content: space-between; align-items: center;
}

.last-checked {
  font-size: 11px; color: var(--el-text-color-placeholder);
  display: flex; align-items: center; gap: 4px;
}

.status-label {
  font-size: 11px; font-weight: 600;
  &.label-up      { color: #67c23a; }
  &.label-down    { color: #f56c6c; }
  &.label-pending { color: #e6a23c; }
  &.label-paused  { color: #909399; }
}

html.dark .monitor-card {
  background: var(--el-bg-color-overlay);
  &:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.35); }
}
</style>

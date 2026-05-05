<template>
  <div class="monitors-page">
    <!-- Page header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Monitors</h1>
        <p class="page-subtitle">Uptime, SSL, and endpoint health across your infrastructure</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAdd">Add Monitor</el-button>
    </div>

    <!-- Stats filter bar -->
    <div class="stats-bar">
      <div
        v-for="pill in pills"
        :key="pill.key"
        :class="['stat-pill', `pill-${pill.key}`, filterStatus === pill.key ? 'active' : '']"
        @click="filterStatus = pill.key as any"
      >
        <span v-if="pill.dot" :class="['pill-dot', `dot-${pill.key}`]" />
        <span class="pill-count">{{ pill.count }}</span>
        <span class="pill-label">{{ pill.label }}</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="monitor-grid">
      <el-skeleton v-for="i in 6" :key="i" :rows="4" animated class="skeleton-card" />
    </div>

    <!-- Empty -->
    <div v-else-if="!filteredMonitors.length" class="empty-state">
      <el-empty
        :description="filterStatus !== 'all' ? `No ${filterStatus} monitors` : 'No monitors yet'"
        :image-size="80"
      >
        <el-button v-if="filterStatus === 'all'" type="primary" :icon="Plus" @click="openAdd">
          Add your first monitor
        </el-button>
      </el-empty>
    </div>

    <!-- Grid -->
    <div v-else class="monitor-grid">
      <MonitorCard
        v-for="m in filteredMonitors"
        :key="m.id"
        :monitor="m"
        :recent-checks="checksMap[m.id]"
        @click="openDetail(m)"
        @edit="openEdit(m)"
        @pause="handlePause(m)"
        @resume="handleResume(m)"
        @delete="handleDelete(m)"
      />
    </div>

    <MonitorForm
      v-model="formVisible"
      :monitor="editingMonitor"
      @submit="handleFormSubmit"
    />

    <MonitorDetail
      v-model="detailVisible"
      :monitor="detailMonitor"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { MonitorsAPI } from '@/api/opspilot/monitors'
import type { Monitor, MonitorCheck, MonitorStats, CreateMonitorRequest } from '@/api/opspilot/monitors'
import MonitorCard from './components/MonitorCard.vue'
import MonitorForm from './components/MonitorForm.vue'
import MonitorDetail from './components/MonitorDetail.vue'

const monitors = ref<Monitor[]>([])
const checksMap = ref<Record<string, MonitorCheck[]>>({})
const stats = ref<MonitorStats>({ total: 0, up: 0, down: 0, paused: 0, pending: 0 })
const loading = ref(false)
const filterStatus = ref<'all' | 'up' | 'down' | 'paused' | 'pending'>('all')

const formVisible = ref(false)
const editingMonitor = ref<Monitor | null>(null)
const detailVisible = ref(false)
const detailMonitor = ref<Monitor | null>(null)

const pills = computed(() => [
  { key: 'all',     label: 'All',     count: stats.value.total,   dot: false },
  { key: 'up',      label: 'Up',      count: stats.value.up,      dot: true },
  { key: 'down',    label: 'Down',    count: stats.value.down,    dot: true },
  { key: 'paused',  label: 'Paused',  count: stats.value.paused,  dot: false },
  { key: 'pending', label: 'Pending', count: stats.value.pending, dot: false },
])

const filteredMonitors = computed(() => {
  if (filterStatus.value === 'all') return monitors.value
  return monitors.value.filter(m => {
    const s = m.enabled ? (m.last_status ?? 'pending') : 'paused'
    return s === filterStatus.value
  })
})

onMounted(load)

async function load() {
  loading.value = true
  try {
    const [list, s] = await Promise.all([MonitorsAPI.list(), MonitorsAPI.getStats()])
    monitors.value = list
    stats.value = s
    list.forEach(m => {
      MonitorsAPI.getChecks(m.id, 24).then(checks => {
        checksMap.value = { ...checksMap.value, [m.id]: checks }
      }).catch(() => {})
    })
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingMonitor.value = null
  formVisible.value = true
}

function openEdit(m: Monitor) {
  editingMonitor.value = m
  formVisible.value = true
}

function openDetail(m: Monitor) {
  detailMonitor.value = m
  detailVisible.value = true
}

async function handleFormSubmit(data: CreateMonitorRequest) {
  if (editingMonitor.value) {
    const updated = await MonitorsAPI.update(editingMonitor.value.id, data)
    replaceMonitor(updated)
    ElMessage.success('Monitor updated')
  } else {
    const created = await MonitorsAPI.create(data)
    monitors.value.unshift(created)
    ElMessage.success('Monitor added')
  }
  stats.value = await MonitorsAPI.getStats()
}

async function handlePause(m: Monitor) {
  const updated = await MonitorsAPI.update(m.id, { enabled: false })
  replaceMonitor(updated)
  stats.value = await MonitorsAPI.getStats()
  ElMessage.success('Monitor paused')
}

async function handleResume(m: Monitor) {
  const updated = await MonitorsAPI.update(m.id, { enabled: true })
  replaceMonitor(updated)
  stats.value = await MonitorsAPI.getStats()
  ElMessage.success('Monitor resumed')
}

async function handleDelete(m: Monitor) {
  await ElMessageBox.confirm(
    `Delete monitor "${m.name}"? This cannot be undone.`,
    'Delete Monitor',
    { type: 'warning', confirmButtonText: 'Delete', confirmButtonClass: 'el-button--danger' }
  ).catch(() => { throw new Error('cancelled') })
  await MonitorsAPI.delete(m.id)
  monitors.value = monitors.value.filter(x => x.id !== m.id)
  stats.value = await MonitorsAPI.getStats()
  ElMessage.success('Monitor deleted')
}

function replaceMonitor(updated: Monitor) {
  const idx = monitors.value.findIndex(m => m.id === updated.id)
  if (idx !== -1) monitors.value[idx] = updated
}
</script>

<style scoped>
.monitors-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.stats-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;

  &:hover { border-color: var(--el-color-primary-light-5); }

  &.active {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }

  &.pill-down.active {
    border-color: #f56c6c;
    background: rgba(245, 108, 108, 0.08);
  }

  &.pill-up.active {
    border-color: #67c23a;
    background: rgba(103, 194, 58, 0.08);
  }
}

.pill-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  &.dot-up   { background: #67c23a; }
  &.dot-down { background: #f56c6c; }
}

.pill-count {
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}

.pill-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.skeleton-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 20px;
  height: 180px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}
</style>

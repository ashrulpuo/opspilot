<template>
  <div class="salt-metrics">
    <!-- Header -->
    <div class="metrics-header">
      <el-row :gutter="20">
        <el-col :span="16">
          <h2>Real-Time Metrics</h2>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-button-group>
            <el-button 
              type="primary" 
              size="small"
              :icon="isConnected ? 'VideoPause' : 'VideoPlay'"
              @click="toggleAutoRefresh"
            >
              {{ isAutoRefresh ? 'Pause' : 'Start' }} Auto Refresh
            </el-button>
            <el-button 
              size="small" 
              @click="refreshMetrics"
              :loading="refreshing"
              :icon="RefreshRight"
            >
              Refresh
            </el-button>
            <el-dropdown trigger="click" @command="handleTimeRange">
              <el-button size="small">
                {{ timeRange.label }}
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    v-for="range in timeRanges" 
                    :key="range.value"
                    :command="range.value"
                  >
                    {{ range.label }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-button-group>
        </el-col>
      </el-row>
    </div>
    
    <!-- CPU Metrics -->
    <el-card shadow="never" class="metrics-card cpu-card">
      <template #header>
        <div class="card-header">
          <el-icon><Cpu /></el-icon>
          <span>CPU Usage</span>
          <span class="card-time">{{ formatLastUpdate(lastCPUUpdate) }}</span>
        </div>
      </template>
      <el-row :gutter="20">
        <!-- Overall CPU Usage -->
        <el-col :span="8">
          <div class="cpu-overall">
            <div class="gauge-title">Overall CPU</div>
            <el-progress 
              type="dashboard"
              :percentage="overallCPU"
              :color="getCPUColor(overallCPU)"
              :stroke-width="20"
              :show-text="true"
              :format="formatProgressText"
            />
          </div>
        </el-col>
        
        <!-- CPU Cores -->
        <el-col :span="16">
          <div class="cpu-cores">
            <div class="section-title">CPU Cores</div>
            <el-scrollbar max-height="300px">
              <div class="cores-grid">
                <div 
                  v-for="core in cpuCores" 
                  :key="core.core"
                  class="core-item"
                >
                  <div class="core-name">{{ core.core }}</div>
                  <el-progress 
                    type="circle"
                    :percentage="core.value"
                    :width="80"
                    :color="getCPUColor(core.value)"
                  />
                  <div class="core-value">{{ core.value.toFixed(1) }}%</div>
                </div>
              </div>
            </el-scrollbar>
          </div>
        </el-col>
      </el-row>
      
      <!-- CPU Breakdown -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <div class="cpu-breakdown">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="User Time">
                <el-progress 
                  :percentage="cpuStats.user || 0"
                  :color="getCPUColor(cpuStats.user || 0)"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span class="metric-value">{{ (cpuStats.user || 0).toFixed(1) }}%</span>
              </el-descriptions-item>
              <el-descriptions-item label="System Time">
                <el-progress 
                  :percentage="cpuStats.system || 0"
                  :color="getCPUColor(cpuStats.system || 0)"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span class="metric-value">{{ (cpuStats.system || 0).toFixed(1) }}%</span>
              </el-descriptions-item>
              <el-descriptions-item label="I/O Wait">
                <el-progress 
                  :percentage="cpuStats.iowait || 0"
                  :color="getCPUColor(cpuStats.iowait || 0)"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span class="metric-value">{{ (cpuStats.iowait || 0).toFixed(1) }}%</span>
              </el-descriptions-item>
              <el-descriptions-item label="Idle">
                <el-progress 
                  :percentage="cpuStats.idle || 0"
                  :color="getCPUColor(cpuStats.idle || 0)"
                  :show-text="false"
                  :stroke-width="8"
                />
                <span class="metric-value">{{ (cpuStats.idle || 0).toFixed(1) }}%</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
        
        <el-col :span="12">
          <div class="cpu-charts">
            <!-- CPU Chart placeholder -->
            <div class="chart-placeholder">
              <el-empty description="CPU Chart" :image-size="200">
                <template #default>
                  <el-icon :size="40" color="#909399"><DataAnalysis /></el-icon>
                </template>
                <template #image>
                  <div style="color: #909399; font-size: 14px;">
                    Real-time CPU chart will be rendered here
                  </div>
                </template>
              </el-empty>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Memory Metrics -->
    <el-card shadow="never" class="metrics-card memory-card">
      <template #header>
        <div class="card-header">
          <el-icon><Memo /></el-icon>
          <span>Memory Usage</span>
          <span class="card-time">{{ formatLastUpdate(lastMemUpdate) }}</span>
        </div>
      </template>
      <el-row :gutter="20">
        <!-- Total Memory -->
        <el-col :span="8">
          <div class="memory-overall">
            <div class="gauge-title">Total Memory</div>
            <div class="memory-value-large">
              {{ formatMemory(memStats.total) }}
            </div>
          </div>
        </el-col>
        
        <!-- Memory Usage -->
        <el-col :span="8">
          <div class="memory-usage">
            <div class="gauge-title">Used / Total</div>
            <div class="memory-ratio">
              <span class="used">{{ formatMemory(memStats.used) }}</span>
              <span class="divider"> / </span>
              <span class="total">{{ formatMemory(memStats.total) }}</span>
            </div>
            <el-progress 
              :percentage="memPercent"
              :color="getMemoryColor(memPercent)"
              :stroke-width="25"
            />
            <div class="memory-percent-text">
              {{ memPercent.toFixed(1) }}% Used
            </div>
          </div>
        </el-col>
        
        <!-- Swap Usage -->
        <el-col :span="8">
          <div class="swap-usage">
            <div class="gauge-title">Swap</div>
            <div class="memory-value">
              {{ formatMemory(memStats.swap_used) }}
            </div>
            <div class="swap-total">
              / {{ formatMemory(memStats.swap_total) }}
            </div>
            <el-progress 
              :percentage="swapPercent"
              :color="getMemoryColor(swapPercent)"
              :stroke-width="15"
            />
            <div class="swap-percent-text">
              {{ swapPercent.toFixed(1) }}%
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Disk Metrics -->
    <el-card shadow="never" class="metrics-card disk-card">
      <template #header>
        <div class="card-header">
          <el-icon><Coin /></el-icon>
          <span>Disk Usage</span>
          <span class="card-time">{{ formatLastUpdate(lastDiskUpdate) }}</span>
        </div>
      </template>
      
      <!-- Disk Usage Bars -->
      <div class="disk-usage">
        <div 
             v-for="disk in diskUsage" 
             :key="disk.mountpoint" 
             class="disk-item"
        >
          <div class="disk-header">
            <span class="disk-name">{{ disk.mountpoint }}</span>
            <span class="disk-size">
              {{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }}
            </span>
          </div>
          <el-progress 
            :percentage="disk.used_percent"
            :color="getDiskColor(disk.used_percent)"
            :stroke-width="20"
            :format="formatProgressText"
          />
          <div class="disk-details">
            <span class="disk-type">{{ disk.fstype }}</span>
            <span class="disk-device">{{ disk.device || '-' }}</span>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- Load Average -->
    <el-card shadow="never" class="metrics-card load-card">
      <template #header>
        <div class="card-header">
          <el-icon><TrendCharts /></el-icon>
          <span>Load Average</span>
          <span class="card-time">{{ formatLastUpdate(lastLoadUpdate) }}</span>
        </div>
      </template>
      <el-row :gutter="30" justify="space-around">
        <el-col :span="8">
          <div class="load-item">
            <div class="load-period">1 Minute</div>
            <div :class="['load-value', getLoadColor(loadAvg['1min'])]">
              {{ loadAvg['1min']?.toFixed(2) || '-' }}
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="load-item">
            <div class="load-period">5 Minutes</div>
            <div :class="['load-value', getLoadColor(loadAvg['5min'])]">
              {{ loadAvg['5min']?.toFixed(2) || '-' }}
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="load-item">
            <div class="load-period">15 Minutes</div>
            <div :class="['load-value', getLoadColor(loadAvg['15min'])]">
              {{ loadAvg['15min']?.toFixed(2) || '-' }}
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { RefreshRight, Cpu, Memo, Coin, TrendCharts, DataAnalysis, VideoPlay, VideoPause } from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'

// Props
const props = defineProps<{
  serverId: string
}>()

// Use SSE composable
const { metrics, isConnected, reconnect, disconnectAll } = useSaltStream(props.serverId)

// Time range options
const timeRanges = [
  { label: '1 Hour', value: '1h' },
  { label: '6 Hours', value: '6h' },
  { label: '24 Hours', value: '24h' },
  { label: '7 Days', value: '7d' },
  { label: '30 Days', value: '30d' }
]

const timeRange = ref(timeRanges[0])
const isAutoRefresh = ref(true)
const refreshing = ref(false)

// Refresh interval
let refreshInterval: any = null

// Computed: CPU metrics
const cpuMetrics = computed(() => {
  const cpu = metrics.value
  const cores: Record<string, any> = {}
  
  // Extract per-core CPU
  Object.values(cpu).forEach(metric => {
    if (metric.metric_name?.startsWith('cpu_') && metric.metric_name?.endsWith('_user')) {
      const coreName = metric.metric_name.split('_')[1]
      cores[coreName] = {
        core: coreName,
        value: metric.metric_value || 0
      }
    }
  })
  
  // Calculate overall CPU
  const coreValues = Object.values(cores).map(c => c.value)
  const avgCPU = coreValues.length > 0 ? coreValues.reduce((a, b) => a + b, 0) / coreValues.length : 0
  
  return {
    cores: cores,
    overallCPU: avgCPU
  }
})

const cpuCores = computed(() => {
  return Object.values(cpuMetrics.value.cores)
})

const overallCPU = computed(() => cpuMetrics.value.overallCPU)

const cpuStats = computed(() => {
  const cpu = metrics.value
  return {
    user: cpu['cpu_total_user']?.metric_value || 0,
    system: cpu['cpu_total_system']?.metric_value || 0,
    iowait: cpu['cpu_total_iowait']?.metric_value || 0,
    idle: cpu['cpu_total_idle']?.metric_value || 0
  }
})

// Computed: Memory metrics
const memStats = computed(() => {
  const mem = metrics.value
  return {
    total: mem['mem_total']?.metric_value || 0,
    available: mem['mem_available']?.metric_value || 0,
    used: (mem['mem_total']?.metric_value || 0) - (mem['mem_available']?.metric_value || 0),
    swap_total: mem['swap_total']?.metric_value || 0,
    swap_used: mem['swap_used']?.metric_value || 0
  }
})

const memPercent = computed(() => {
  const { total, available } = memStats.value
  if (!total || total === 0) return 0
  return ((total - available) / total) * 100
})

const swapPercent = computed(() => {
  const { swap_total, swap_used } = memStats.value
  if (!swap_total || swap_total === 0) return 0
  return (swap_used / swap_total) * 100
})

// Computed: Disk metrics
const diskUsage = computed(() => {
  const disk = metrics.value
  const disks: any[] = []
  
  // Extract disk usage per mount point
  Object.values(disk).forEach(metric => {
    if (metric.metric_name?.startsWith('disk_usage_')) {
      const mountpoint = metric.metric_name.replace('disk_usage_', '').replace('_', '/')
      disks.push({
        mountpoint: mountpoint.startsWith('/') ? mountpoint : `/${mountpoint}`,
        used: metric.metadata?.used_gb || 0,
        total: metric.metadata?.total_gb || 0,
        used_percent: metric.metric_value || 0,
        fstype: metric.metadata?.fstype || '',
        device: metric.metadata?.device || ''
      })
    }
  })
  
  return disks
})

// Computed: Load average
const loadAvg = computed(() => {
  const load = metrics.value
  return {
    '1min': load['load_1min']?.metric_value || 0,
    '5min': load['load_5min']?.metric_value || 0,
    '15min': load['load_15min']?.metric_value || 0
  }
})

// Computed: Last update times
const lastCPUUpdate = computed(() => {
  const cpu = metrics.value['cpu_0_user']
  return cpu ? cpu.timestamp : null
})

const lastMemUpdate = computed(() => {
  const mem = metrics.value['memory_percent']
  return mem ? mem.timestamp : null
})

const lastDiskUpdate = computed(() => {
  const disk = metrics.value['disk_usage__']
  return disk ? disk.timestamp : null
})

const lastLoadUpdate = computed(() => {
  const load = metrics.value['load_1min']
  return load ? load.timestamp : null
})

// Helper functions
const formatMemory = (bytes: number | undefined) => {
  if (!bytes) return 'Unknown'
  
  const gb = bytes / (1024 ** 3)
  const mb = bytes / (1024 ** 2)
  
  if (gb >= 1) return `${gb.toFixed(2)} GB`
  if (mb >= 1) return `${mb.toFixed(0)} MB`
  return `${bytes} B`
}

const formatBytes = (bytes: number | undefined) => {
  if (!bytes) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes
  let unitIndex = 0
  
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex++
  }
  
  return `${value.toFixed(2)} ${units[unitIndex]}`
}

const formatProgressText = (percentage: number) => {
  return `${percentage.toFixed(1)}%`
}

const formatLastUpdate = (timestamp: string | null) => {
  if (!timestamp) return '-'
  
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 120000) return '1m ago'
  if (diffMs < 300000) return '5m ago'
  return 'More than 5m ago'
}

// Color helper functions
const getCPUColor = (value: number) => {
  if (value < 50) return '#67C23A'
  if (value < 70) return '#E6A23C'
  if (value < 85) return '#F59E0B'
  return '#F56C6C'
}

const getMemoryColor = (value: number) => {
  if (value < 50) return '#67C23A'
  if (value < 70) return '#E6A23C'
  if (value < 85) return '#F59E0B'
  return '#F56C6C'
}

const getDiskColor = (value: number) => {
  if (value < 70) return '#67C23A'
  if (value < 85) return '#E6A23C'
  if (value < 90) return '#F59E0B'
  return '#F56C6C'
}

const getLoadColor = (value: number) => {
  const numCores = cpuCores.value.length || 1
  
  if (value < numCores) return '#67C23A'
  if (value < numCores * 2) return '#E6A23C'
  if (value < numCores * 3) return '#F59E0B'
  return '#F56C6C'
}

// Actions
const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value
  
  if (isAutoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  // SSE provides real-time updates, so auto-refresh is for periodic full data fetch
  // This would be used if SSE connection is lost
  console.log('Auto-refresh enabled')
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
    console.log('Auto-refresh disabled')
  }
}

const refreshMetrics = async () => {
  refreshing.value = true
  
  try {
    // This would trigger a full metrics fetch via API
    // For now, we'll simulate it
    console.log('Refreshing metrics...')
    
    await new Promise(resolve => setTimeout(resolve, 1000))
  } catch (error) {
    console.error('Failed to refresh metrics:', error)
  } finally {
    refreshing.value = false
  }
}

const handleTimeRange = (range: string) => {
  const selected = timeRanges.find(r => r.value === range)
  if (selected) {
    timeRange.value = selected
    console.log('Time range changed to:', selected.label)
    // This would update the chart to show data for selected range
  }
}

// Lifecycle
onMounted(() => {
  console.log('Salt Metrics component mounted for server:', props.serverId)
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.salt-metrics {
  padding: 20px;
}

.metrics-header {
  margin-bottom: 20px;
}

.metrics-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}

.card-time {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

/* CPU Styles */
.cpu-overall {
  padding: 20px;
}

.gauge-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.cpu-overall :deep(.el-progress__text) {
  font-size: 24px;
}

.cpu-cores {
  border-left: 1px solid #DCDFE6;
  padding-left: 20px;
}

.section-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
  font-weight: 600;
}

.cores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 15px;
}

.core-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  background: #F5F7FA;
}

.core-name {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 600;
}

.core-item :deep(.el-progress) {
  margin-bottom: 8px;
}

.core-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.cpu-breakdown {
  background: #F5F7FA;
  padding: 15px;
  border-radius: 4px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.cpu-charts {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  width: 100%;
  height: 100%;
}

/* Memory Styles */
.memory-overall {
  padding: 20px;
}

.memory-value-large {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 10px;
}

.memory-usage {
  padding: 20px;
}

.gauge-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.memory-ratio {
  font-size: 16px;
  color: #303133;
  margin-bottom: 10px;
}

.divider {
  margin: 0 5px;
  color: #909399;
}

.memory-percent-text {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-top: 5px;
}

.swap-usage {
  padding: 20px;
}

.memory-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.swap-total {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.swap-percent-text {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-top: 5px;
}

/* Disk Styles */
.disk-usage {
  padding: 0;
}

.disk-item {
  padding: 20px;
  border-bottom: 1px solid #EBEEF5;
}

.disk-item:last-child {
  border-bottom: none;
}

.disk-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.disk-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.disk-size {
  font-size: 13px;
  color: #606266;
}

.disk-item :deep(.el-progress-bar__outer) {
  margin-bottom: 10px;
}

.disk-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.disk-type {
  font-weight: 500;
}

.disk-device {
  font-family: 'JetBrains Mono', monospace;
}

/* Load Styles */
.load-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.load-card :deep(.el-card__header) {
  background: transparent;
  color: white;
  border-bottom: none;
}

.load-item {
  text-align: center;
  padding: 20px;
}

.load-period {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 10px;
}

.load-value {
  font-size: 32px;
  font-weight: 700;
  color: white;
}

.load-value.status-online {
  color: #67C23A;
}

.load-value.status-warning {
  color: #E6A23C;
}

.load-value.status-critical {
  color: #F56C6C;
}
</style>

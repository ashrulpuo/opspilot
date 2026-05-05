<template>
  <div class="server-overview">
    <el-row :gutter="20">
      <!-- Server Info Card -->
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <span>Server Information</span>
              <el-button
                size="small"
                type="primary"
                :loading="redeploying"
                :icon="Refresh"
                @click="redeployAgent"
              >Redeploy Agent</el-button>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Server Name" :span="2">
              {{ displayName }}
            </el-descriptions-item>
            <el-descriptions-item label="Hostname">
              {{ displayHostname }}
            </el-descriptions-item>
            <el-descriptions-item label="IP Address">
              {{ displayIp }}
            </el-descriptions-item>
            <el-descriptions-item label="OS">
              {{ displayOs }}
            </el-descriptions-item>
            <el-descriptions-item label="Architecture">
              {{ displayArch }}
            </el-descriptions-item>
            <el-descriptions-item label="CPU Cores">
              {{ displayCores }}
            </el-descriptions-item>
            <el-descriptions-item label="Memory">
              {{ displayMemory }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <!-- Quick Stats Card -->
      <el-col :span="12">
        <el-card shadow="never" header="Quick Stats">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-label">CPU Usage</div>
                <div class="stat-value">{{ quickStats.cpu_percent }}%</div>
                <el-progress :percentage="Math.min(100, quickStats.cpu_percent)" :show-text="false" />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-label">Memory Usage</div>
                <div class="stat-value">{{ quickStats.memory_percent }}%</div>
                <el-progress :percentage="Math.min(100, quickStats.memory_percent)" :show-text="false" />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-label">Disk Usage</div>
                <div class="stat-value">{{ quickStats.disk_percent }}%</div>
                <el-progress :percentage="Math.min(100, quickStats.disk_percent)" :show-text="false" />
              </div>
            </el-col>
          </el-row>
          
          <el-divider />
          
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="mini-stat">
                <el-icon><Coin /></el-icon>
                <div>
                  <div class="mini-stat-label">Services</div>
                  <div class="mini-stat-value">{{ quickStats.service_count }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="mini-stat">
                <el-icon><Operation /></el-icon>
                <div>
                  <div class="mini-stat-label">Processes</div>
                  <div class="mini-stat-value">{{ quickStats.process_count }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Recent Alerts -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="never" header="Recent Alerts">
          <el-table :data="panelAlerts" stripe>
            <el-table-column prop="alert_type" label="Type" width="150" />
            <el-table-column prop="message" label="Message" />
            <el-table-column prop="severity" label="Severity" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Time" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty 
            v-if="panelAlerts.length === 0" 
            description="No recent alerts"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Coin, Operation, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { ServersAPI } from '@/api/opspilot/servers'
import { useServerStore } from '@/stores/server'
import { useSaltStore } from '@/composables/useSaltStream'

import type { Server, ServerOverviewPanel } from '@/api/opspilot/types'

const props = defineProps<{
  serverId: string
}>()

const serverStore = useServerStore()
const saltStore = useSaltStore()

const apiServer = ref<Server | null>(null)
const panel = ref<ServerOverviewPanel | null>(null)

const server = computed(() => {
  const fromStore = serverStore.servers[props.serverId]
  const fromApi = apiServer.value
  return { ...fromStore, ...fromApi } as Server & Record<string, unknown>
})

// Read a live SSE metric from the Pinia store (keyed as `{serverId}_{name}`)
const sseMetric = (name: string): number | null => {
  const m = saltStore.metrics[`${props.serverId}_${name}`]
  return m != null ? m.metric_value : null
}

// Quick stats — SSE store values update in realtime; REST panel is the initial/fallback
const quickStats = computed(() => {
  const cpu =
    sseMetric('cpu_percent') ??
    sseMetric('cpu_usage') ??
    panel.value?.quick_stats.cpu_percent ?? 0

  const mem =
    sseMetric('memory_percent') ??
    sseMetric('memory_used_percent') ??
    panel.value?.quick_stats.memory_percent ?? 0

  const disk =
    sseMetric('disk_usage_percent') ??
    sseMetric('disk_usage') ??
    panel.value?.quick_stats.disk_percent ?? 0

  const sseServiceCount = sseMetric('service_count')
  const svcCount =
    sseServiceCount !== null ? Math.round(sseServiceCount) :
    Object.values(saltStore.services).filter(s => s.server_id === props.serverId).length ||
    (panel.value?.quick_stats.service_count ?? 0)

  const sseProcCount = sseMetric('process_count')
  const procCount =
    sseProcCount !== null ? Math.round(sseProcCount) :
    saltStore.processes.filter(p => p.server_id === props.serverId).length ||
    (panel.value?.quick_stats.process_count ?? 0)

  return {
    cpu_percent: Math.round(cpu * 10) / 10,
    memory_percent: Math.round(mem * 10) / 10,
    disk_percent: Math.round(disk * 10) / 10,
    service_count: svcCount,
    process_count: procCount,
  }
})

const panelAlerts = computed(() => {
  const sseAlerts = saltStore.alerts
    .filter(a => a.server_id === props.serverId)
    .slice(0, 5)
    .map(a => ({
      alert_type: a.alert_type,
      message: a.message,
      severity: a.severity,
      created_at: a.created_at,
    }))
  return sseAlerts.length > 0 ? sseAlerts : (panel.value?.recent_alerts ?? [])
})

const displayName = computed(() => server.value.name || (server.value as any).hostname || '-')

const displayHostname = computed(() =>
  (server.value as any).agent_reported_hostname ||
  (server.value as any).hostname ||
  server.value.ip_address || '-'
)

const displayIp = computed(() =>
  (server.value as any).agent_reported_ip || server.value.ip_address || '-'
)

const displayOs = computed(() => {
  const s = server.value as any
  const parts = [s.os_name || s.agent_os_name, s.os_version || s.agent_os_version].filter(Boolean)
  if (parts.length) return parts.join(' ')
  return s.os_type || '-'
})

const displayArch = computed(() => {
  const s = server.value as any
  return s.architecture || s.agent_architecture || '-'
})

const displayCores = computed(() => {
  const s = server.value as any
  const cores = s.cpu_cores ?? s.agent_cpu_cores
  return cores != null ? String(cores) : '-'
})

const formatMemory = (mb: number | undefined | null) => {
  if (mb == null || mb === 0) return '-'
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

const displayMemory = computed(() => {
  const s = server.value as any
  return formatMemory(s.memory_mb ?? s.agent_memory_mb)
})

const redeploying = ref(false)

const redeployAgent = async () => {
  redeploying.value = true
  try {
    await ServersAPI.redeployAgent(props.serverId)
    ElMessage.success('Agent redeploy started — server info will update in ~60s')
  } catch (e: any) {
    ElMessage.error(e?.message ?? 'Redeploy failed')
  } finally {
    redeploying.value = false
  }
}

const load = async () => {
  try {
    const [s, p] = await Promise.all([
      ServersAPI.get(props.serverId),
      ServersAPI.getOverviewPanel(props.serverId),
    ])
    apiServer.value = s
    panel.value = p
  } catch (e) {
    console.warn('[ServerOverview] failed to load panel', e)
  }
}

onMounted(load)

const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'critical': return 'danger'
    case 'warning': return 'warning'
    default: return 'info'
  }
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`
  return date.toLocaleString()
}
</script>

<style scoped>
.server-overview {
  padding: 20px;
}

.stat-item {
  text-align: center;
  padding: 10px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.mini-stat {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.mini-stat .el-icon {
  font-size: 30px;
  color: #606266;
}

.mini-stat-label {
  font-size: 12px;
  color: #909399;
}

.mini-stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
</style>

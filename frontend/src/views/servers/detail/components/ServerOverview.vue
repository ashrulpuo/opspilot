<template>
  <div class="server-overview">
    <el-row :gutter="20">
      <!-- Server Info Card -->
      <el-col :span="12">
        <el-card shadow="never" header="Server Information">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Server Name" :span="2">
              {{ server.name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Hostname">
              {{ server.hostname || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="IP Address">
              {{ server.ip_address || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="OS">
              {{ server.os_name || '-' }} {{ server.os_version || '' }}
            </el-descriptions-item>
            <el-descriptions-item label="Architecture">
              {{ server.architecture || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="CPU Cores">
              {{ server.cpu_cores || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Memory">
              {{ formatMemory(server.memory_mb) }}
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
                <div class="stat-value">{{ cpuUsage }}%</div>
                <el-progress :percentage="cpuUsage" :show-text="false" />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-label">Memory Usage</div>
                <div class="stat-value">{{ memUsage }}%</div>
                <el-progress :percentage="memUsage" :show-text="false" />
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-label">Disk Usage</div>
                <div class="stat-value">{{ diskUsage }}%</div>
                <el-progress :percentage="diskUsage" :show-text="false" />
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
                  <div class="mini-stat-value">{{ serviceCount }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="mini-stat">
                <el-icon><Operation /></el-icon>
                <div>
                  <div class="mini-stat-label">Processes</div>
                  <div class="mini-stat-value">{{ processCount }}</div>
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
          <el-table :data="recentAlerts" stripe>
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
            v-if="recentAlerts.length === 0" 
            description="No recent alerts"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Coin, Operation } from '@element-plus/icons-vue'

import { useServerStore } from '@/stores/server'
import { useSaltStream } from '@/composables/useSaltStream'

const props = defineProps<{
  serverId: string
}>()

const serverStore = useServerStore()
const { alerts, services, metrics } = useSaltStream(props.serverId)

const server = computed(() => serverStore.servers[props.serverId] || {})

// Quick stats (mock values for now)
const cpuUsage = computed(() => {
  // In production, this would come from metrics
  return 45
})

const memUsage = computed(() => {
  // In production, this would come from metrics
  return 62
})

const diskUsage = computed(() => {
  // In production, this would come from metrics
  return 38
})

// Counts
const serviceCount = computed(() => {
  return Object.values(services.value).filter(s => s.server_id === props.serverId).length
})

const processCount = computed(() => {
  return metrics.value.filter(m => m.server_id === props.serverId && m.metric_name === 'process_count')[0]?.metric_value || 0
})

// Recent alerts
const recentAlerts = computed(() => {
  return alerts.value
    .filter(a => a.server_id === props.serverId)
    .slice(0, 5)
})

// Helper functions
const formatMemory = (mb: number | undefined) => {
  if (!mb) return '-'
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'critical': return 'danger'
    case 'warning': return 'warning'
    case 'info': return 'info'
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

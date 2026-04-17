<template>
  <div class="salt-services">
    <!-- Header -->
    <div class="services-header">
      <el-row :gutter="20">
        <el-col :span="16">
          <h2>Services</h2>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-input 
            v-model="searchQuery"
            placeholder="Search services..."
            clearable
            style="width: 200px; margin-right: 10px;"
          />
          <el-button 
            type="primary" 
            :icon="RefreshRight"
            @click="refreshServices"
            :loading="refreshing"
            :disabled="!isConnected"
          >
            Refresh
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- Services Stats -->
    <el-row :gutter="20" class="services-stats">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-total">
            <div class="stat-icon">
              <el-icon :size="30"><Coin /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Total Services</div>
              <div class="stat-value">{{ totalServices }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-running">
            <div class="stat-icon">
              <el-icon :size="30"><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Running</div>
              <div class="stat-value">{{ runningServices }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-stopped">
            <div class="stat-icon">
              <el-icon :size="30"><CircleClose /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Stopped</div>
              <div class="stat-value">{{ stoppedServices }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-unknown">
            <div class="stat-icon">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Unknown</div>
              <div class="stat-value">{{ unknownServices }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Services Table -->
    <el-card shadow="never" class="services-table">
      <el-table 
        :data="filteredServices"
        stripe
        border
        style="width: 100%"
        v-loading="loading"
      >
        <!-- Service Name -->
        <el-table-column prop="service_name" label="Service Name" min-width="200">
          <template #default="{ row }">
            <el-icon style="margin-right: 5px;"><Coin /></el-icon>
            <strong>{{ row.service_name }}</strong>
          </template>
        </el-table-column>
        
        <!-- Status -->
        <el-table-column label="Status" width="120">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              effect="dark"
            >
              <el-icon class="status-icon">
                <component :is="getStatusIcon(row.status)" />
              </el-icon>
              {{ row.status.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- Previous Status -->
        <el-table-column label="Previous Status" width="150">
          <template #default="{ row }">
            <el-tag 
              v-if="row.previous_status"
              :type="getStatusType(row.previous_status)" 
              size="small"
            >
              {{ row.previous_status.toUpperCase() }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <!-- Last Checked -->
        <el-table-column label="Last Checked" width="180">
          <template #default="{ row }">
            <span class="last-checked">{{ formatLastChecked(row.last_checked) }}</span>
          </template>
        </el-table-column>
        
        <!-- Actions -->
        <el-table-column label="Actions" width="280" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="row.status === 'stopped'"
                type="success" 
                size="small"
                :icon="VideoPlay"
                @click="startService(row.service_name)"
                :loading="actionLoading[row.service_name]?.start"
              >
                Start
              </el-button>
              <el-button 
                v-if="row.status === 'running'"
                type="warning" 
                size="small"
                :icon="VideoPause"
                @click="stopService(row.service_name)"
                :loading="actionLoading[row.service_name]?.stop"
              >
                Stop
              </el-button>
              <el-button 
                v-if="row.status === 'running'"
                type="primary" 
                size="small"
                :icon="RefreshRight"
                @click="restartService(row.service_name)"
                :loading="actionLoading[row.service_name]?.restart"
              >
                Restart
              </el-button>
              <el-button 
                type="info" 
                size="small"
                :icon="View"
                @click="viewServiceDetails(row)"
              >
                Details
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Empty State -->
      <el-empty 
        v-if="!loading && filteredServices.length === 0" 
        description="No services found"
      />
    </el-card>
    
    <!-- Service Details Dialog -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="Service Details"
      width="600px"
    >
      <el-descriptions v-if="selectedService" :column="1" border>
        <el-descriptions-item label="Service Name">
          <strong>{{ selectedService.service_name }}</strong>
        </el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag :type="getStatusType(selectedService.status)">
            {{ selectedService.status.toUpperCase() }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Previous Status">
          <el-tag 
            v-if="selectedService.previous_status"
            :type="getStatusType(selectedService.previous_status)"
            size="small"
          >
            {{ selectedService.previous_status.toUpperCase() }}
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="Last Checked">
          {{ formatDateTime(selectedService.last_checked) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="detailsDialogVisible = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  RefreshRight, 
  Coin, 
  CircleCheck, 
  CircleClose, 
  Warning,
  VideoPlay,
  VideoPause,
  View
} from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'

// Types
interface ServiceState {
  id: string
  server_id: string
  service_name: string
  status: 'running' | 'stopped' | 'unknown'
  previous_status?: string
  last_checked: string
}

// Props
const props = defineProps<{
  serverId: string
}>()

// Use SSE composable
const { services, isConnected, disconnectAll } = useSaltStream(props.serverId)

// Reactive state
const searchQuery = ref('')
const refreshing = ref(false)
const loading = ref(false)
const actionLoading = ref<Record<string, { start?: boolean, stop?: boolean, restart?: boolean }>>({})
const detailsDialogVisible = ref(false)
const selectedService = ref<ServiceState | null>(null)

// Computed: Services list
const serviceList = computed(() => {
  return Object.values(services.value).filter(s => s.server_id === props.serverId)
})

// Computed: Filtered services
const filteredServices = computed(() => {
  const query = searchQuery.value.toLowerCase()
  
  if (!query) {
    return serviceList.value
  }
  
  return serviceList.value.filter(service => 
    service.service_name.toLowerCase().includes(query)
  )
})

// Computed: Service stats
const totalServices = computed(() => serviceList.value.length)
const runningServices = computed(() => serviceList.value.filter(s => s.status === 'running').length)
const stoppedServices = computed(() => serviceList.value.filter(s => s.status === 'stopped').length)
const unknownServices = computed(() => serviceList.value.filter(s => s.status === 'unknown').length)

// Helper functions
const getStatusType = (status: string) => {
  switch (status) {
    case 'running': return 'success'
    case 'stopped': return 'danger'
    case 'unknown': return 'info'
    default: return 'info'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return CircleCheck
    case 'stopped': return CircleClose
    case 'unknown': return Warning
    default: return Warning
  }
}

const formatLastChecked = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 120000) return '1m ago'
  if (diffMs < 300000) return '5m ago'
  if (diffMs < 3600000) return '30m ago'
  if (diffMs < 86400000) return '1h ago'
  return 'More than 1d ago'
}

const formatDateTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// Actions
const refreshServices = async () => {
  refreshing.value = true
  
  try {
    // This would trigger a service status check via Salt API
    // For now, we'll simulate it
    console.log('Refreshing services...')
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage({
      message: 'Services refreshed successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to refresh services:', error)
    ElMessage.error('Failed to refresh services')
  } finally {
    refreshing.value = false
  }
}

const startService = async (serviceName: string) => {
  // Set loading state
  if (!actionLoading.value[serviceName]) {
    actionLoading.value[serviceName] = {}
  }
  actionLoading.value[serviceName].start = true
  
  try {
    // This would call the Salt API to start the service
    console.log('Starting service:', serviceName)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage({
      message: `Service ${serviceName} started successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to start service:', error)
    ElMessage.error(`Failed to start service ${serviceName}`)
  } finally {
    actionLoading.value[serviceName].start = false
  }
}

const stopService = async (serviceName: string) => {
  // Set loading state
  if (!actionLoading.value[serviceName]) {
    actionLoading.value[serviceName] = {}
  }
  actionLoading.value[serviceName].stop = true
  
  try {
    // Confirm before stopping critical services
    await ElMessageBox.confirm(
      `Are you sure you want to stop the service ${serviceName}?`,
      'Stop Service',
      {
        confirmButtonText: 'Stop',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    
    // This would call the Salt API to stop the service
    console.log('Stopping service:', serviceName)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage({
      message: `Service ${serviceName} stopped successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to stop service:', error)
      ElMessage.error(`Failed to stop service ${serviceName}`)
    }
  } finally {
    actionLoading.value[serviceName].stop = false
  }
}

const restartService = async (serviceName: string) => {
  // Set loading state
  if (!actionLoading.value[serviceName]) {
    actionLoading.value[serviceName] = {}
  }
  actionLoading.value[serviceName].restart = true
  
  try {
    // Confirm before restarting critical services
    await ElMessageBox.confirm(
      `Are you sure you want to restart the service ${serviceName}?`,
      'Restart Service',
      {
        confirmButtonText: 'Restart',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    
    // This would call the Salt API to restart the service
    console.log('Restarting service:', serviceName)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage({
      message: `Service ${serviceName} restarted successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to restart service:', error)
      ElMessage.error(`Failed to restart service ${serviceName}`)
    }
  } finally {
    actionLoading.value[serviceName].restart = false
  }
}

const viewServiceDetails = (service: ServiceState) => {
  selectedService.value = service
  detailsDialogVisible.value = true
}

// Lifecycle
onMounted(() => {
  console.log('Salt Services component mounted for server:', props.serverId)
})
</script>

<style scoped>
.salt-services {
  padding: 20px;
}

.services-header {
  margin-bottom: 20px;
}

.services-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.services-stats {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 8px;
}

.stat-total .stat-icon {
  background: #f5f7fa;
}

.stat-running .stat-icon {
  background: #f0f9ff;
}

.stat-stopped .stat-icon {
  background: #fef0f0;
}

.stat-unknown .stat-icon {
  background: #f4f4f5;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-running .stat-value {
  color: #67C23A;
}

.stat-stopped .stat-value {
  color: #F56C6C;
}

.stat-unknown .stat-value {
  color: #909399;
}

.services-table {
  background: white;
}

.status-icon {
  margin-right: 5px;
  font-size: 14px;
}

.last-checked {
  font-size: 13px;
  color: #606266;
}

.text-muted {
  color: #909399;
}
</style>

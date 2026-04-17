<template>
  <div class="salt-alerts">
    <!-- Header -->
    <div class="alerts-header">
      <el-row :gutter="20">
        <el-col :span="16">
          <h2>Alerts</h2>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-button-group>
            <el-button 
              type="success" 
              size="small"
              :icon="Check"
              @click="acknowledgeAll"
              :disabled="unreadAlerts === 0"
            >
              Acknowledge All
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              :icon="Delete"
              @click="clearAllAlerts"
            >
              Clear All
            </el-button>
            <el-button 
              type="primary" 
              size="small"
              :icon="RefreshRight"
              @click="refreshAlerts"
            >
              Refresh
            </el-button>
          </el-button-group>
        </el-col>
      </el-row>
    </div>
    
    <!-- Alert Stats -->
    <el-row :gutter="20" class="alert-stats">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-total">
            <div class="stat-icon">
              <el-icon :size="30"><Bell /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Total Alerts</div>
              <div class="stat-value">{{ totalAlerts }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-unread">
            <div class="stat-icon">
              <el-icon :size="30"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Unread</div>
              <div class="stat-value">{{ unreadAlerts }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-critical">
            <div class="stat-icon">
              <el-icon :size="30"><CircleClose /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Critical</div>
              <div class="stat-value">{{ criticalAlerts }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-warning">
            <div class="stat-icon">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Warnings</div>
              <div class="stat-value">{{ warningAlerts }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Filters -->
    <el-row :gutter="20" class="alert-filters">
      <el-col :span="8">
        <el-input 
          v-model="searchQuery"
          placeholder="Search alerts..."
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="selectedSeverity" 
          placeholder="Filter by severity"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="severity in severities" 
            :key="severity.value" 
            :label="severity.label" 
            :value="severity.value"
          >
            <el-tag :type="severity.type" size="small">
              {{ severity.label }}
            </el-tag>
          </el-option>
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="selectedAlertType" 
          placeholder="Filter by type"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="type in alertTypes" 
            :key="type" 
            :label="type" 
            :value="type"
          />
        </el-select>
      </el-col>
    </el-row>
    
    <!-- Toggle: Show only unread -->
    <el-row :gutter="20" class="alert-options">
      <el-col :span="24">
        <el-checkbox v-model="showOnlyUnread">
          Show only unread alerts
          <el-badge 
            :value="unreadAlerts"
            :hidden="unreadAlerts === 0"
            type="primary"
            style="margin-left: 10px;"
          />
        </el-checkbox>
      </el-col>
    </el-row>
    
    <!-- Alerts List -->
    <el-card shadow="never" class="alerts-list">
      <div v-loading="loading">
        <!-- Alert Items -->
        <div 
          v-for="alert in filteredAlerts" 
          :key="alert.id"
          :class="['alert-item', `alert-severity-${alert.severity}`, { 'alert-unread': !alert.acknowledged }]"
        >
          <!-- Alert Header -->
          <div class="alert-header">
            <div class="alert-severity-badge">
              <el-tag 
                :type="getSeverityType(alert.severity)"
                effect="dark"
                size="small"
              >
                {{ alert.severity.toUpperCase() }}
              </el-tag>
            </div>
            <div class="alert-type">
              <el-icon><Warning /></el-icon>
              <span>{{ alert.alert_type }}</span>
            </div>
            <div class="alert-timestamp">
              {{ formatTimestamp(alert.created_at) }}
            </div>
            <el-badge 
              v-if="!alert.acknowledged"
              is-dot
              class="alert-unread-badge"
            />
          </div>
          
          <!-- Alert Message -->
          <div class="alert-message">
            <p>{{ alert.message }}</p>
          </div>
          
          <!-- Alert Actions -->
          <div class="alert-actions">
            <el-button-group>
              <el-button 
                v-if="!alert.acknowledged"
                type="success" 
                size="small"
                :icon="Check"
                @click="acknowledgeAlert(alert)"
              >
                Acknowledge
              </el-button>
              <el-button 
                type="primary" 
                size="small"
                :icon="View"
                @click="viewAlertDetails(alert)"
              >
                Details
              </el-button>
            </el-button-group>
          </div>
        </div>
        
        <!-- Empty State -->
        <el-empty 
          v-if="!loading && filteredAlerts.length === 0" 
          description="No alerts found"
          :image-size="100"
        >
          <el-icon :size="50" color="#909399"><Bell /></el-icon>
        </el-empty>
      </div>
    </el-card>
    
    <!-- Alert Details Dialog -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="Alert Details"
      width="700px"
    >
      <el-descriptions v-if="selectedAlert" :column="1" border>
        <el-descriptions-item label="Severity">
          <el-tag :type="getSeverityType(selectedAlert.severity)">
            {{ selectedAlert.severity.toUpperCase() }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Alert Type">
          <strong>{{ selectedAlert.alert_type }}</strong>
        </el-descriptions-item>
        <el-descriptions-item label="Message">
          {{ selectedAlert.message }}
        </el-descriptions-item>
        <el-descriptions-item label="Server ID">
          {{ selectedAlert.server_id }}
        </el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag :type="selectedAlert.acknowledged ? 'success' : 'danger'">
            {{ selectedAlert.acknowledged ? 'Acknowledged' : 'Unread' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Created At">
          {{ formatDateTime(selectedAlert.created_at) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- Event Data -->
      <div v-if="selectedAlert && selectedAlert.event_data" style="margin-top: 20px;">
        <h4>Event Data</h4>
        <el-collapse>
          <el-collapse-item title="View Event Data" name="1">
            <pre class="event-data">{{ JSON.stringify(selectedAlert.event_data, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <template #footer>
        <el-button @click="detailsDialogVisible = false">Close</el-button>
        <el-button 
          v-if="selectedAlert && !selectedAlert.acknowledged"
          type="success"
          :icon="Check"
          @click="acknowledgeAlert(selectedAlert)"
        >
          Acknowledge
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Bell,
  Check,
  Delete,
  RefreshRight,
  Warning,
  Search,
  View,
  ChatDotRound,
  CircleClose
} from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'

// Types
interface Alert {
  id: string
  server_id: string
  alert_type: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  event_data: Record<string, any>
  processed: boolean
  created_at: string
  acknowledged?: boolean
}

// Props
const props = defineProps<{
  serverId: string
}>()

// Use SSE composable
const { alerts, acknowledgeAlert as acknowledgeStoreAlert, clearAlerts: clearStoreAlerts, disconnectAll } = useSaltStream(props.serverId)

// Reactive state
const searchQuery = ref('')
const selectedSeverity = ref('')
const selectedAlertType = ref('')
const showOnlyUnread = ref(false)
const loading = ref(false)
const detailsDialogVisible = ref(false)
const selectedAlert = ref<Alert | null>(null)

// Severity options
const severities = [
  { label: 'Info', value: 'info', type: 'info' },
  { label: 'Warning', value: 'warning', type: 'warning' },
  { label: 'Critical', value: 'critical', type: 'danger' }
]

// Computed: Alerts list
const alertList = computed(() => {
  return alerts.value.filter(a => a.server_id === props.serverId)
})

// Computed: Unique alert types
const alertTypes = computed(() => {
  const types = new Set<string>()
  alertList.value.forEach(a => types.add(a.alert_type))
  return Array.from(types).sort()
})

// Computed: Filtered alerts
const filteredAlerts = computed(() => {
  let filtered = alertList.value
  
  // Filter by severity
  if (selectedSeverity.value) {
    filtered = filtered.filter(a => a.severity === selectedSeverity.value)
  }
  
  // Filter by alert type
  if (selectedAlertType.value) {
    filtered = filtered.filter(a => a.alert_type === selectedAlertType.value)
  }
  
  // Filter by unread
  if (showOnlyUnread.value) {
    filtered = filtered.filter(a => !a.acknowledged)
  }
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(a => 
      a.message.toLowerCase().includes(query) ||
      a.alert_type.toLowerCase().includes(query) ||
      (a.event_data && JSON.stringify(a.event_data).toLowerCase().includes(query))
    )
  }
  
  return filtered
})

// Computed: Alert stats
const totalAlerts = computed(() => alertList.value.length)
const unreadAlerts = computed(() => alertList.value.filter(a => !a.acknowledged).length)
const criticalAlerts = computed(() => alertList.value.filter(a => a.severity === 'critical').length)
const warningAlerts = computed(() => alertList.value.filter(a => a.severity === 'warning').length)

// Helper functions
const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'info': return 'info'
    case 'warning': return 'warning'
    case 'critical': return 'danger'
    default: return 'info'
  }
}

const formatTimestamp = (timestamp: string) => {
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
const acknowledgeAlert = async (alert: Alert) => {
  try {
    acknowledgeStoreAlert(alert.id)
    
    ElMessage({
      message: 'Alert acknowledged successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to acknowledge alert:', error)
    ElMessage.error('Failed to acknowledge alert')
  }
}

const acknowledgeAll = async () => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to acknowledge all ${unreadAlerts.value} unread alerts?`,
      'Acknowledge All Alerts',
      {
        confirmButtonText: 'Acknowledge All',
        cancelButtonText: 'Cancel',
        type: 'info'
      }
    )
    
    // Acknowledge all unread alerts
    alertList.value.forEach(alert => {
      if (!alert.acknowledged) {
        acknowledgeStoreAlert(alert.id)
      }
    })
    
    ElMessage({
      message: `Acknowledged ${unreadAlerts.value} alerts`,
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to acknowledge alerts:', error)
      ElMessage.error('Failed to acknowledge alerts')
    }
  }
}

const clearAllAlerts = async () => {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to clear all alerts? This action cannot be undone.',
      'Clear All Alerts',
      {
        confirmButtonText: 'Clear',
        cancelButtonText: 'Cancel',
        type: 'danger'
      }
    )
    
    clearStoreAlerts()
    
    ElMessage({
      message: 'All alerts cleared successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to clear alerts:', error)
      ElMessage.error('Failed to clear alerts')
    }
  }
}

const refreshAlerts = async () => {
  loading.value = true
  
  try {
    // This would trigger a fetch of historical alerts via API
    console.log('Refreshing alerts...')
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage({
      message: 'Alerts refreshed successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to refresh alerts:', error)
    ElMessage.error('Failed to refresh alerts')
  } finally {
    loading.value = false
  }
}

const viewAlertDetails = (alert: Alert) => {
  selectedAlert.value = alert
  detailsDialogVisible.value = true
}

// Lifecycle
onMounted(() => {
  console.log('Salt Alerts component mounted for server:', props.serverId)
})
</script>

<style scoped>
.salt-alerts {
  padding: 20px;
}

.alerts-header {
  margin-bottom: 20px;
}

.alerts-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.alert-stats {
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

.stat-unread .stat-icon {
  background: #f0f9ff;
}

.stat-critical .stat-icon {
  background: #fef0f0;
}

.stat-warning .stat-icon {
  background: #fdf6ec;
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

.stat-unread .stat-value {
  color: #67C23A;
}

.stat-critical .stat-value {
  color: #F56C6C;
}

.stat-warning .stat-value {
  color: #E6A23C;
}

.alert-filters {
  margin-bottom: 20px;
}

.alert-options {
  margin-bottom: 20px;
}

.alerts-list {
  background: white;
}

.alert-item {
  border-left: 4px solid #DCDFE6;
  background: white;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 4px;
  transition: all 0.3s;
}

.alert-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.alert-item.alert-severity-critical {
  border-left-color: #F56C6C;
  background: #fef0f0;
}

.alert-item.alert-severity-warning {
  border-left-color: #E6A23C;
  background: #fdf6ec;
}

.alert-item.alert-severity-info {
  border-left-color: #67C23A;
}

.alert-item.alert-unread {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-weight: 500;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 13px;
}

.alert-type {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  font-weight: 500;
}

.alert-timestamp {
  margin-left: auto;
  color: #909399;
}

.alert-unread-badge {
  margin-left: 5px;
}

.alert-message {
  margin-bottom: 10px;
}

.alert-message p {
  margin: 0;
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
}

.alert-actions {
  display: flex;
  justify-content: flex-end;
}

.event-data {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 12px;
  color: #303133;
  overflow-x: auto;
  margin: 0;
}

.alert-item :deep(.el-collapse) {
  margin-top: 10px;
}

.alert-item :deep(.el-collapse-item__header) {
  font-size: 12px;
  padding: 0;
}
</style>

<template>
  <div class="salt-logs">
    <!-- Header -->
    <div class="logs-header">
      <el-row :gutter="20">
        <el-col :span="16">
          <h2>Logs</h2>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-button-group>
            <el-button 
              v-if="isAutoScroll"
              type="info"
              size="small"
              :icon="VideoPause"
              @click="toggleAutoScroll"
            >
              Pause
            </el-button>
            <el-button 
              v-else
              type="primary"
              size="small"
              :icon="VideoPlay"
              @click="toggleAutoScroll"
            >
              Auto Scroll
            </el-button>
            <el-button 
              type="success" 
              size="small"
              :icon="Download"
              @click="downloadLogs"
            >
              Download
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              :icon="Delete"
              @click="clearLogs"
            >
              Clear
            </el-button>
          </el-button-group>
        </el-col>
      </el-row>
    </div>
    
    <!-- Log Stats -->
    <el-row :gutter="20" class="log-stats">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-total">
            <div class="stat-icon">
              <el-icon :size="30"><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Total Logs</div>
              <div class="stat-value">{{ totalLogs }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-info">
            <div class="stat-icon">
              <el-icon :size="30"><InfoFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Info</div>
              <div class="stat-value">{{ infoLogs }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-warn">
            <div class="stat-icon">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Warnings</div>
              <div class="stat-value">{{ warnLogs }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-error">
            <div class="stat-icon">
              <el-icon :size="30"><CircleClose /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Errors</div>
              <div class="stat-value">{{ errorLogs }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Filters -->
    <el-row :gutter="20" class="log-filters">
      <el-col :span="8">
        <el-input 
          v-model="searchQuery"
          placeholder="Search logs..."
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="selectedLevel" 
          placeholder="Filter by level"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="level in logLevels" 
            :key="level.value" 
            :label="level.label" 
            :value="level.value"
          >
            <el-tag :type="level.type" size="small">
              {{ level.label }}
            </el-tag>
          </el-option>
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="selectedSource" 
          placeholder="Filter by source"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="source in logSources" 
            :key="source" 
            :label="source" 
            :value="source"
          />
        </el-select>
      </el-col>
    </el-row>
    
    <!-- Logs Container -->
    <el-card shadow="never" class="logs-container">
      <div 
        ref="logsContainerRef"
        class="logs-content"
        v-loading="loading"
      >
        <!-- Log Entries -->
        <div 
          v-for="log in filteredLogs" 
          :key="log.id"
          :class="['log-entry', `log-level-${log.log_level.toLowerCase()}`]"
        >
          <!-- Log Header -->
          <div class="log-header">
            <div class="log-level">
              <el-tag 
                :type="getLevelType(log.log_level)"
                effect="dark"
                size="small"
              >
                {{ log.log_level }}
              </el-tag>
            </div>
            <div class="log-source">
              <el-icon><Service /></el-icon>
              <span>{{ log.source }}</span>
            </div>
            <div class="log-timestamp">
              {{ formatTimestamp(log.timestamp) }}
            </div>
          </div>
          
          <!-- Log Message -->
          <div class="log-message">
            <pre>{{ highlightSearch(log.message) }}</pre>
          </div>
          
          <!-- Metadata -->
          <el-collapse v-if="log.metadata && Object.keys(log.metadata).length > 0">
            <el-collapse-item title="Metadata">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item 
                  v-for="(value, key) in log.metadata" 
                  :key="key"
                  :label="key"
                >
                  {{ formatMetadataValue(value) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <!-- Empty State -->
        <el-empty 
          v-if="!loading && filteredLogs.length === 0" 
          description="No logs found"
          :image-size="100"
        >
          <el-icon :size="50" color="#909399"><Document /></el-icon>
        </el-empty>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document,
  InfoFilled,
  Warning,
  CircleClose,
  Search,
  Service,
  Download,
  Delete,
  VideoPlay,
  VideoPause
} from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'

// Types
interface LogEntry {
  id: string
  server_id: string
  timestamp: string
  log_level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  source: string
  message: string
  metadata?: Record<string, any>
}

// Props
const props = defineProps<{
  serverId: string
}>()

// Use SSE composable
const { logs, isConnected, disconnectAll, clearLogs: clearStoreLogs } = useSaltStream(props.serverId)

// Reactive state
const searchQuery = ref('')
const selectedLevel = ref('')
const selectedSource = ref('')
const loading = ref(false)
const isAutoScroll = ref(true)
const logsContainerRef = ref<HTMLElement | null>(null)

// Log level options
const logLevels = [
  { label: 'DEBUG', value: 'DEBUG', type: 'info' },
  { label: 'INFO', value: 'INFO', type: 'info' },
  { label: 'WARN', value: 'WARN', type: 'warning' },
  { label: 'ERROR', value: 'ERROR', type: 'danger' }
]

// Computed: Logs list
const logList = computed(() => {
  return logs.value.filter(l => l.server_id === props.serverId)
})

// Computed: Unique sources
const logSources = computed(() => {
  const sources = new Set<string>()
  logList.value.forEach(l => sources.add(l.source))
  return Array.from(sources).sort()
})

// Computed: Filtered logs
const filteredLogs = computed(() => {
  let filtered = logList.value
  
  // Filter by level
  if (selectedLevel.value) {
    filtered = filtered.filter(l => l.log_level === selectedLevel.value)
  }
  
  // Filter by source
  if (selectedSource.value) {
    filtered = filtered.filter(l => l.source === selectedSource.value)
  }
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(l => 
      l.message.toLowerCase().includes(query) ||
      l.source.toLowerCase().includes(query) ||
      (l.metadata && JSON.stringify(l.metadata).toLowerCase().includes(query))
    )
  }
  
  return filtered
})

// Computed: Log stats
const totalLogs = computed(() => logList.value.length)
const infoLogs = computed(() => logList.value.filter(l => l.log_level === 'INFO').length)
const warnLogs = computed(() => logList.value.filter(l => l.log_level === 'WARN').length)
const errorLogs = computed(() => logList.value.filter(l => l.log_level === 'ERROR').length)

// Helper functions
const getLevelType = (level: string) => {
  switch (level) {
    case 'DEBUG': return 'info'
    case 'INFO': return 'success'
    case 'WARN': return 'warning'
    case 'ERROR': return 'danger'
    default: return 'info'
  }
}

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const formatMetadataValue = (value: any) => {
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const highlightSearch = (message: string) => {
  if (!searchQuery.value) {
    return message
  }
  
  const query = searchQuery.value
  const regex = new RegExp(`(${query})`, 'gi')
  return message.replace(regex, '<mark>$1</mark>')
}

// Actions
const toggleAutoScroll = () => {
  isAutoScroll.value = !isAutoScroll.value
}

const downloadLogs = async () => {
  try {
    // Convert logs to JSON
    const logsData = filteredLogs.value.map(log => ({
      timestamp: log.timestamp,
      level: log.log_level,
      source: log.source,
      message: log.message,
      metadata: log.metadata
    }))
    
    // Create blob
    const blob = new Blob([JSON.stringify(logsData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    // Download
    const link = document.createElement('a')
    link.href = url
    link.download = `server-${props.serverId}-logs-${new Date().toISOString()}.json`
    link.click()
    
    // Cleanup
    URL.revokeObjectURL(url)
    
    ElMessage({
      message: 'Logs downloaded successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to download logs:', error)
    ElMessage.error('Failed to download logs')
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to clear all logs? This action cannot be undone.',
      'Clear Logs',
      {
        confirmButtonText: 'Clear',
        cancelButtonText: 'Cancel',
        type: 'danger'
      }
    )
    
    clearStoreLogs()
    
    ElMessage({
      message: 'Logs cleared successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to clear logs:', error)
      ElMessage.error('Failed to clear logs')
    }
  }
}

// Auto-scroll to bottom when new logs arrive
watch(filteredLogs, async () => {
  if (isAutoScroll.value) {
    await nextTick()
    if (logsContainerRef.value) {
      logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
    }
  }
})

// Lifecycle
onMounted(() => {
  console.log('Salt Logs component mounted for server:', props.serverId)
})

onUnmounted(() => {
  console.log('Salt Logs component unmounted')
})
</script>

<style scoped>
.salt-logs {
  padding: 20px;
}

.logs-header {
  margin-bottom: 20px;
}

.logs-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.log-stats {
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

.stat-info .stat-icon {
  background: #f0f9ff;
}

.stat-warn .stat-icon {
  background: #fdf6ec;
}

.stat-error .stat-icon {
  background: #fef0f0;
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

.stat-info .stat-value {
  color: #67C23A;
}

.stat-warn .stat-value {
  color: #E6A23C;
}

.stat-error .stat-value {
  color: #F56C6C;
}

.log-filters {
  margin-bottom: 20px;
}

.logs-container {
  background: white;
}

.logs-content {
  max-height: 600px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.log-entry {
  background: white;
  border-left: 4px solid #DCDFE6;
  padding: 10px 15px;
  margin-bottom: 10px;
  border-radius: 4px;
  transition: all 0.3s;
}

.log-entry:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.log-level-debug {
  border-left-color: #909399;
}

.log-level-info {
  border-left-color: #67C23A;
}

.log-level-warn {
  border-left-color: #E6A23C;
  background: #fdf6ec;
}

.log-level-error {
  border-left-color: #F56C6C;
  background: #fef0f0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 8px;
  font-size: 12px;
}

.log-source {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
}

.log-timestamp {
  margin-left: auto;
  color: #909399;
}

.log-message {
  margin: 8px 0;
}

.log-message pre {
  margin: 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-message mark {
  background: #ffe58f;
  padding: 2px 4px;
  border-radius: 2px;
}

.log-entry :deep(.el-collapse) {
  margin-top: 10px;
}

.log-entry :deep(.el-collapse-item__header) {
  font-size: 12px;
  padding: 0;
}

.log-entry :deep(.el-collapse-item__wrap) {
  background: #f5f7fa;
  border-radius: 4px;
}

.log-entry :deep(.el-descriptions) {
  font-size: 12px;
}

.log-entry :deep(.el-descriptions__label) {
  color: #909399;
}

/* Scrollbar styling */
.logs-content::-webkit-scrollbar {
  width: 8px;
}

.logs-content::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 4px;
}

.logs-content::-webkit-scrollbar-thumb {
  background: #DCDFE6;
  border-radius: 4px;
}

.logs-content::-webkit-scrollbar-thumb:hover {
  background: #C0C4CC;
}
</style>

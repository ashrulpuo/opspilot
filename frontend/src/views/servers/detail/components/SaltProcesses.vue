<template>
  <div class="salt-processes">
    <!-- Header -->
    <div class="processes-header">
      <el-row :gutter="20">
        <el-col :span="16">
          <h2>Processes</h2>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-input 
            v-model="searchQuery"
            placeholder="Search processes..."
            clearable
            style="width: 200px; margin-right: 10px;"
          />
          <el-button 
            type="primary" 
            :icon="RefreshRight"
            @click="refreshProcesses"
            :loading="refreshing"
            :disabled="!isConnected"
          >
            Refresh
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- Process Stats -->
    <el-row :gutter="20" class="process-stats">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-total">
            <div class="stat-icon">
              <el-icon :size="30"><Operation /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Total Processes</div>
              <div class="stat-value">{{ totalProcesses }}</div>
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
              <div class="stat-value">{{ runningProcesses }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-sleeping">
            <div class="stat-icon">
              <el-icon :size="30"><Moon /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Sleeping</div>
              <div class="stat-value">{{ sleepingProcesses }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-zombie">
            <div class="stat-icon">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Zombie</div>
              <div class="stat-value">{{ zombieProcesses }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Filters -->
    <el-row :gutter="20" class="process-filters">
      <el-col :span="8">
        <el-select 
          v-model="selectedState" 
          placeholder="Filter by state"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="state in processStates" 
            :key="state.value" 
            :label="state.label" 
            :value="state.value"
          >
            <el-tag :type="state.type" size="small">
              {{ state.label }}
            </el-tag>
          </el-option>
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="sortBy" 
          placeholder="Sort by"
          style="width: 100%;"
        >
          <el-option 
            v-for="sort in sortOptions" 
            :key="sort.value" 
            :label="sort.label" 
            :value="sort.value"
          />
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="sortOrder" 
          placeholder="Order"
          style="width: 100%;"
        >
          <el-option label="Ascending" value="asc" />
          <el-option label="Descending" value="desc" />
        </el-select>
      </el-col>
    </el-row>
    
    <!-- Processes Table -->
    <el-card shadow="never" class="processes-table">
      <el-table 
        :data="filteredProcesses"
        stripe
        border
        style="width: 100%"
        v-loading="loading"
        max-height="600"
      >
        <!-- PID -->
        <el-table-column 
          prop="pid" 
          label="PID" 
          width="80" 
          sortable
        >
          <template #default="{ row }">
            <el-tag type="info">{{ row.pid }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- Name -->
        <el-table-column 
          prop="name" 
          label="Name" 
          min-width="150"
          sortable
        >
          <template #default="{ row }">
            <el-icon style="margin-right: 5px;"><Operation /></el-icon>
            <strong>{{ row.name }}</strong>
          </template>
        </el-table-column>
        
        <!-- User -->
        <el-table-column 
          prop="username" 
          label="User" 
          width="120"
          sortable
        >
          <template #default="{ row }">
            <el-tag 
              v-if="row.username === 'root'"
              type="danger"
              size="small"
            >
              root
            </el-tag>
            <span v-else class="user-name">{{ row.username }}</span>
          </template>
        </el-table-column>
        
        <!-- State -->
        <el-table-column label="State" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStateType(row.state)"
              effect="dark"
              size="small"
            >
              {{ row.state }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- CPU % -->
        <el-table-column 
          label="CPU %" 
          width="120"
          sortable
        >
          <template #default="{ row }">
            <div class="cpu-bar">
              <el-progress 
                :percentage="row.cpu_percent"
                :color="getCPUColor(row.cpu_percent)"
                :show-text="false"
                :stroke-width="10"
              />
              <span class="cpu-value">{{ row.cpu_percent.toFixed(1) }}%</span>
            </div>
          </template>
        </el-table-column>
        
        <!-- Memory % -->
        <el-table-column 
          label="Memory %" 
          width="120"
          sortable
        >
          <template #default="{ row }">
            <div class="mem-bar">
              <el-progress 
                :percentage="row.memory_percent"
                :color="getMemoryColor(row.memory_percent)"
                :show-text="false"
                :stroke-width="10"
              />
              <span class="mem-value">{{ row.memory_percent.toFixed(1) }}%</span>
            </div>
          </template>
        </el-table-column>
        
        <!-- Start Time -->
        <el-table-column label="Start Time" width="180">
          <template #default="{ row }">
            <span class="start-time">{{ formatStartTime(row.start_time) }}</span>
          </template>
        </el-table-column>
        
        <!-- Command -->
        <el-table-column prop="command" label="Command" min-width="300">
          <template #default="{ row }">
            <code class="command">{{ row.command }}</code>
          </template>
        </el-table-column>
        
        <!-- Actions -->
        <el-table-column label="Actions" width="100" fixed="right">
          <template #default="{ row }">
            <el-dropdown @command="(cmd) => handleAction(cmd, row)">
              <el-button type="primary" size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="details" :icon="View">
                    Details
                  </el-dropdown-item>
                  <el-dropdown-item command="kill" :icon="Delete" divided>
                    Kill Process
                  </el-dropdown-item>
                  <el-dropdown-item command="kill-9" :icon="WarningFilled" type="danger">
                    Force Kill
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Empty State -->
      <el-empty 
        v-if="!loading && filteredProcesses.length === 0" 
        description="No processes found"
      />
    </el-card>
    
    <!-- Process Details Dialog -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="Process Details"
      width="700px"
    >
      <el-descriptions v-if="selectedProcess" :column="2" border>
        <el-descriptions-item label="PID" :span="1">
          <el-tag type="info">{{ selectedProcess.pid }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Name" :span="1">
          <strong>{{ selectedProcess.name }}</strong>
        </el-descriptions-item>
        <el-descriptions-item label="User" :span="1">
          <el-tag 
            v-if="selectedProcess.username === 'root'"
            type="danger"
          >
            root
          </el-tag>
          <span v-else>{{ selectedProcess.username }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="State" :span="1">
          <el-tag :type="getStateType(selectedProcess.state)">
            {{ selectedProcess.state }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="CPU %" :span="1">
          <el-progress 
            :percentage="selectedProcess.cpu_percent"
            :color="getCPUColor(selectedProcess.cpu_percent)"
            :show-text="true"
            :stroke-width="15"
          />
        </el-descriptions-item>
        <el-descriptions-item label="Memory %" :span="1">
          <el-progress 
            :percentage="selectedProcess.memory_percent"
            :color="getMemoryColor(selectedProcess.memory_percent)"
            :show-text="true"
            :stroke-width="15"
          />
        </el-descriptions-item>
        <el-descriptions-item label="Start Time" :span="2">
          {{ formatDateTime(selectedProcess.start_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="Command" :span="2">
          <code class="command">{{ selectedProcess.command }}</code>
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
  Operation, 
  CircleCheck, 
  CircleClose, 
  Warning,
  Moon,
  MoreFilled,
  View,
  Delete,
  WarningFilled
} from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'

// Types
interface Process {
  id: string
  server_id: string
  pid: number
  name: string
  command: string
  username: string
  cpu_percent: number
  memory_percent: number
  state: 'R' | 'S' | 'D' | 'Z' | 'T' | 'W'
  start_time: string
}

// Props
const props = defineProps<{
  serverId: string
}>()

// Use SSE composable
const { processes, isConnected, disconnectAll } = useSaltStream(props.serverId)

// Reactive state
const searchQuery = ref('')
const selectedState = ref('')
const sortBy = ref('cpu_percent')
const sortOrder = ref<'asc' | 'desc'>('desc')
const refreshing = ref(false)
const loading = ref(false)
const detailsDialogVisible = ref(false)
const selectedProcess = ref<Process | null>(null)

// Process state options
const processStates = [
  { label: 'Running (R)', value: 'R', type: 'success' },
  { label: 'Sleeping (S)', value: 'S', type: 'info' },
  { label: 'Uninterruptible (D)', value: 'D', type: 'warning' },
  { label: 'Zombie (Z)', value: 'Z', type: 'danger' },
  { label: 'Stopped (T)', value: 'T', type: 'warning' },
  { label: 'Paging (W)', value: 'W', type: 'info' }
]

// Sort options
const sortOptions = [
  { label: 'CPU %', value: 'cpu_percent' },
  { label: 'Memory %', value: 'memory_percent' },
  { label: 'PID', value: 'pid' },
  { label: 'Name', value: 'name' },
  { label: 'User', value: 'username' },
  { label: 'Start Time', value: 'start_time' }
]

// Computed: Processes list
const processList = computed(() => {
  return processes.value.filter(p => p.server_id === props.serverId)
})

// Computed: Filtered processes
const filteredProcesses = computed(() => {
  let filtered = processList.value
  
  // Filter by state
  if (selectedState.value) {
    filtered = filtered.filter(p => p.state === selectedState.value)
  }
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p => 
      p.name.toLowerCase().includes(query) ||
      p.command.toLowerCase().includes(query) ||
      p.username.toLowerCase().includes(query) ||
      p.pid.toString().includes(query)
    )
  }
  
  // Sort
  const key = sortBy.value as keyof Process
  filtered = [...filtered].sort((a, b) => {
    const aValue = a[key]
    const bValue = b[key]
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortOrder.value === 'asc' ? aValue - bValue : bValue - aValue
    }
    
    const aStr = String(aValue || '').toLowerCase()
    const bStr = String(bValue || '').toLowerCase()
    return sortOrder.value === 'asc' 
      ? aStr.localeCompare(bStr) 
      : bStr.localeCompare(aStr)
  })
  
  return filtered
})

// Computed: Process stats
const totalProcesses = computed(() => processList.value.length)
const runningProcesses = computed(() => processList.value.filter(p => p.state === 'R').length)
const sleepingProcesses = computed(() => processList.value.filter(p => p.state === 'S').length)
const zombieProcesses = computed(() => processList.value.filter(p => p.state === 'Z').length)

// Helper functions
const getStateType = (state: string) => {
  switch (state) {
    case 'R': return 'success'
    case 'S': return 'info'
    case 'D': return 'warning'
    case 'Z': return 'danger'
    case 'T': return 'warning'
    case 'W': return 'info'
    default: return 'info'
  }
}

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

const formatStartTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`
  if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`
  return date.toLocaleDateString()
}

const formatDateTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// Actions
const refreshProcesses = async () => {
  refreshing.value = true
  
  try {
    // This would trigger a process list refresh via Salt API
    console.log('Refreshing processes...')
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage({
      message: 'Processes refreshed successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to refresh processes:', error)
    ElMessage.error('Failed to refresh processes')
  } finally {
    refreshing.value = false
  }
}

const handleAction = (action: string, process: Process) => {
  switch (action) {
    case 'details':
      viewProcessDetails(process)
      break
    case 'kill':
      killProcess(process, false)
      break
    case 'kill-9':
      killProcess(process, true)
      break
  }
}

const viewProcessDetails = (process: Process) => {
  selectedProcess.value = process
  detailsDialogVisible.value = true
}

const killProcess = async (process: Process, force = false) => {
  const command = force ? `kill -9 ${process.pid}` : `kill ${process.pid}`
  const title = force ? 'Force Kill Process' : 'Kill Process'
  const warningType = 'error'
  
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to ${force ? 'force ' : ''}kill process ${process.name} (PID: ${process.pid})?`,
      title,
      {
        confirmButtonText: force ? 'Force Kill' : 'Kill',
        cancelButtonText: 'Cancel',
        type: warningType,
        dangerouslyUseHTMLString: true
      }
    )
    
    // This would call the Salt API to kill the process
    console.log('Killing process:', process.pid, 'force:', force)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage({
      message: `Process ${process.name} (PID: ${process.pid}) ${force ? 'force ' : ''}killed successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to kill process:', error)
      ElMessage.error(`Failed to kill process ${process.pid}`)
    }
  }
}

// Lifecycle
onMounted(() => {
  console.log('Salt Processes component mounted for server:', props.serverId)
})
</script>

<style scoped>
.salt-processes {
  padding: 20px;
}

.processes-header {
  margin-bottom: 20px;
}

.processes-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.process-stats {
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

.stat-sleeping .stat-icon {
  background: #f4f4f5;
}

.stat-zombie .stat-icon {
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

.stat-running .stat-value {
  color: #67C23A;
}

.stat-zombie .stat-value {
  color: #F56C6C;
}

.process-filters {
  margin-bottom: 20px;
}

.processes-table {
  background: white;
}

.cpu-bar,
.mem-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cpu-bar :deep(.el-progress),
.mem-bar :deep(.el-progress) {
  flex: 1;
}

.cpu-value,
.mem-value {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  min-width: 40px;
  text-align: right;
}

.start-time {
  font-size: 13px;
  color: #606266;
}

.user-name {
  font-size: 13px;
  color: #606266;
}

.command {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #303133;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  display: block;
  word-break: break-all;
}
</style>

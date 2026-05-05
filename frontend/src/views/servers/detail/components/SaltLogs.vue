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
              type="primary"
              size="small"
              :icon="RefreshRight"
              :loading="loading"
              @click="fetchLogs(1)"
            >
              Refresh
            </el-button>
            <el-button
              type="success"
              size="small"
              :icon="Download"
              @click="downloadLogs"
            >
              Download
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
            <div class="stat-icon"><el-icon :size="30"><Document /></el-icon></div>
            <div class="stat-content">
              <div class="stat-label">Total Logs</div>
              <div class="stat-value">{{ stats.total }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-info">
            <div class="stat-icon"><el-icon :size="30"><InfoFilled /></el-icon></div>
            <div class="stat-content">
              <div class="stat-label">Info</div>
              <div class="stat-value">{{ stats.info }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-warn">
            <div class="stat-icon"><el-icon :size="30"><Warning /></el-icon></div>
            <div class="stat-content">
              <div class="stat-label">Warnings</div>
              <div class="stat-value">{{ stats.warn }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-error">
            <div class="stat-icon"><el-icon :size="30"><CircleClose /></el-icon></div>
            <div class="stat-content">
              <div class="stat-label">Errors</div>
              <div class="stat-value">{{ stats.error }}</div>
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
          @input="onSearchInput"
          @clear="fetchLogs(1)"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </el-col>
      <el-col :span="8">
        <el-select
          v-model="selectedLevel"
          placeholder="Filter by level"
          clearable
          style="width: 100%;"
          @change="fetchLogs(1)"
        >
          <el-option
            v-for="level in logLevels"
            :key="level.value"
            :label="level.label"
            :value="level.value"
          >
            <el-tag :type="level.type" size="small">{{ level.label }}</el-tag>
          </el-option>
        </el-select>
      </el-col>
    </el-row>

    <!-- Source chips -->
    <div class="source-chips" v-if="sourceStats.length > 0">
      <el-tag
        :class="['source-chip', selectedSource === '' ? 'chip-active' : '']"
        size="default"
        @click="selectSource('')"
      >
        All
        <span class="chip-count">{{ stats.total }}</span>
      </el-tag>
      <el-tag
        v-for="s in sourceStats"
        :key="s.source"
        :class="['source-chip', selectedSource === s.source ? 'chip-active' : '']"
        size="default"
        @click="selectSource(s.source)"
      >
        {{ s.source }}
        <span class="chip-count">{{ s.count }}</span>
      </el-tag>
    </div>

    <!-- Logs Container -->
    <el-card shadow="never" class="logs-container">
      <div class="logs-content" v-loading="loading">
        <div
          v-for="(log, idx) in logItems"
          :key="log.id"
          :class="['log-entry', `log-level-${log.log_level.toLowerCase()}`]"
          @click="openDrawer(idx)"
        >
          <div class="log-header">
            <div class="log-level">
              <el-tag :type="getLevelType(log.log_level)" effect="dark" size="small">
                {{ log.log_level }}
              </el-tag>
            </div>
            <div class="log-source">
              <el-icon><Service /></el-icon>
              <span>{{ log.source }}</span>
            </div>
            <div class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</div>
            <el-icon class="log-expand-hint"><ArrowRight /></el-icon>
          </div>
          <div class="log-message">
            <pre>{{ truncateMessage(log.message) }}</pre>
          </div>
        </div>

        <el-empty
          v-if="!loading && logItems.length === 0"
          description="No logs found"
          :image-size="100"
        >
          <el-icon :size="50" color="#909399"><Document /></el-icon>
        </el-empty>
      </div>

      <!-- Pagination -->
      <div class="logs-pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[25, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchLogs"
          @size-change="onPageSizeChange"
        />
      </div>
    </el-card>

    <!-- Log Detail Drawer -->
    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="50%"
      :with-header="false"
      class="log-detail-drawer"
    >
      <div v-if="activeLog" class="drawer-content">
        <div class="drawer-header">
          <div class="drawer-title-row">
            <el-tag :type="getLevelType(activeLog.log_level)" effect="dark" size="default">
              {{ activeLog.log_level }}
            </el-tag>
            <span class="drawer-source">
              <el-icon><Service /></el-icon>
              {{ activeLog.source }}
            </span>
            <span class="drawer-ts">{{ formatTimestamp(activeLog.timestamp) }}</span>
          </div>
          <div class="drawer-actions">
            <el-button-group>
              <el-button size="small" :disabled="activeIndex === 0" @click="navigate(-1)">
                <el-icon><ArrowLeft /></el-icon> Prev
              </el-button>
              <el-button size="small" :disabled="activeIndex === logItems.length - 1" @click="navigate(1)">
                Next <el-icon><ArrowRight /></el-icon>
              </el-button>
            </el-button-group>
            <el-button size="small" :icon="CopyDocument" @click="copyMessage">Copy</el-button>
            <el-button size="small" :icon="Close" @click="drawerVisible = false" />
          </div>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-label">Message</div>
          <pre class="drawer-message">{{ activeLog.message }}</pre>
        </div>

        <div v-if="activeLog.extra && Object.keys(activeLog.extra).length > 0" class="drawer-section">
          <div class="drawer-section-label">Extra</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item
              v-for="(value, key) in activeLog.extra"
              :key="key"
              :label="String(key)"
            >
              <pre class="extra-value">{{ formatMetadataValue(value) }}</pre>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="drawer-nav-hint">{{ activeIndex + 1 }} / {{ logItems.length }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document, InfoFilled, Warning, CircleClose,
  Search, Service, Download, RefreshRight,
  ArrowLeft, ArrowRight, CopyDocument, Close,
} from '@element-plus/icons-vue'
import request from '@/api/opspilot/client'

interface LogEntry {
  id: string
  timestamp: string
  log_level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  source: string
  message: string
  extra?: Record<string, any>
}

interface LogStats {
  total: number
  info: number
  warn: number
  error: number
  debug: number
}

interface LogsPagedResponse {
  items: LogEntry[]
  total: number
  page: number
  page_size: number
  total_pages: number
  stats: LogStats
}

const props = defineProps<{ serverId: string }>()

const logItems = ref<LogEntry[]>([])
const stats = ref<LogStats>({ total: 0, info: 0, warn: 0, error: 0, debug: 0 })
const sourceStats = ref<{ source: string; count: number }[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const searchQuery = ref('')
const selectedLevel = ref('')
const selectedSource = ref('')
let refreshTimer: ReturnType<typeof setInterval> | null = null
let searchDebounce: ReturnType<typeof setTimeout> | null = null

const logLevels = [
  { label: 'DEBUG', value: 'DEBUG', type: 'info' },
  { label: 'INFO',  value: 'INFO',  type: 'info' },
  { label: 'WARN',  value: 'WARN',  type: 'warning' },
  { label: 'ERROR', value: 'ERROR', type: 'danger' },
]

const fetchLogs = async (page = currentPage.value) => {
  loading.value = true
  currentPage.value = page
  try {
    const params: Record<string, any> = { page, page_size: pageSize.value }
    if (selectedLevel.value) { params.level = selectedLevel.value }
    if (selectedSource.value) { params.source = selectedSource.value }
    if (searchQuery.value) { params.search = searchQuery.value }

    const data = await request.get<LogsPagedResponse>(
      `/servers/${props.serverId}/salt/logs`,
      { params }
    )
    logItems.value = data.items ?? []
    total.value = data.total ?? 0
    stats.value = data.stats ?? { total: 0, info: 0, warn: 0, error: 0, debug: 0 }
  } catch {
    // empty state shown
  } finally {
    loading.value = false
  }
}

const fetchSourceStats = async () => {
  try {
    const data = await request.get<{ source: string; count: number }[]>(
      `/servers/${props.serverId}/salt/logs/source-stats`
    )
    sourceStats.value = Array.isArray(data) ? data : []
  } catch {
    // ignore
  }
}

const selectSource = (src: string) => {
  selectedSource.value = src
  fetchLogs(1)
}

const onSearchInput = () => {
  if (searchDebounce) { clearTimeout(searchDebounce) }
  searchDebounce = setTimeout(() => fetchLogs(1), 300)
}

const onPageSizeChange = () => fetchLogs(1)

// Drawer state
const drawerVisible = ref(false)
const activeIndex = ref(0)
const activeLog = computed(() => logItems.value[activeIndex.value] ?? null)

const openDrawer = (idx: number) => {
  activeIndex.value = idx
  drawerVisible.value = true
}

const navigate = (delta: number) => {
  const next = activeIndex.value + delta
  if (next >= 0 && next < logItems.value.length) { activeIndex.value = next }
}

const copyMessage = () => {
  if (!activeLog.value) { return }
  navigator.clipboard.writeText(activeLog.value.message).then(() => {
    ElMessage({ message: 'Copied', type: 'success', duration: 1500 })
  })
}

const truncateMessage = (msg: string) => {
  return msg.length > 300 ? msg.slice(0, 300) + '…' : msg
}

const getLevelType = (level: string) => {
  switch (level) {
    case 'INFO':  return 'success'
    case 'WARN':  return 'warning'
    case 'ERROR': return 'danger'
    default:      return 'info'
  }
}

const formatTimestamp = (ts: string) => new Date(ts).toLocaleString()

const formatMetadataValue = (value: any) =>
  typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)

const downloadLogs = async () => {
  try {
    const params: Record<string, any> = { page: 1, page_size: 5000 }
    if (selectedLevel.value) { params.level = selectedLevel.value }
    if (selectedSource.value) { params.source = selectedSource.value }
    if (searchQuery.value) { params.search = searchQuery.value }

    const data = await request.get<LogsPagedResponse>(
      `/servers/${props.serverId}/salt/logs`,
      { params }
    )
    const blob = new Blob([JSON.stringify(data.items, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `server-${props.serverId}-logs-${new Date().toISOString()}.json`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage({ message: 'Logs downloaded', type: 'success', duration: 2000 })
  } catch {
    ElMessage.error('Failed to download logs')
  }
}

onMounted(() => {
  fetchLogs(1)
  fetchSourceStats()
  // auto-refresh only on page 1 (live tail)
  refreshTimer = setInterval(() => {
    if (currentPage.value === 1) { fetchLogs(1) }
  }, 30_000)
})

onUnmounted(() => {
  if (refreshTimer) { clearInterval(refreshTimer) }
  if (searchDebounce) { clearTimeout(searchDebounce) }
})
</script>

<style scoped>
.salt-logs { padding: 20px; }

.logs-header { margin-bottom: 20px; }
.logs-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: #303133; }

.log-stats { margin-bottom: 20px; }

.stat-card { display: flex; align-items: center; gap: 20px; }
.stat-icon {
  display: flex; align-items: center; justify-content: center;
  width: 60px; height: 60px; border-radius: 8px;
}
.stat-total .stat-icon { background: #f5f7fa; }
.stat-info  .stat-icon { background: #f0f9ff; }
.stat-warn  .stat-icon { background: #fdf6ec; }
.stat-error .stat-icon { background: #fef0f0; }

.stat-content { flex: 1; }
.stat-label { font-size: 12px; color: #909399; margin-bottom: 5px; }
.stat-value { font-size: 24px; font-weight: 600; color: #303133; }
.stat-info  .stat-value { color: #67C23A; }
.stat-warn  .stat-value { color: #E6A23C; }
.stat-error .stat-value { color: #F56C6C; }

.log-filters { margin-bottom: 12px; }

.source-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.source-chip {
  cursor: pointer;
  user-select: none;
  border-color: #DCDFE6;
  background: #f5f7fa;
  color: #606266;
  transition: all 0.2s;
}
.source-chip:hover { border-color: #409EFF; color: #409EFF; background: #ecf5ff; }
.source-chip.chip-active { border-color: #409EFF; background: #409EFF; color: #fff; }
.chip-count {
  display: inline-block;
  margin-left: 5px;
  font-size: 11px;
  opacity: 0.8;
}

.logs-container { background: white; }

.logs-content {
  min-height: 200px;
  max-height: 560px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.logs-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0 4px;
}

.log-entry {
  background: white;
  border-left: 4px solid #DCDFE6;
  padding: 10px 15px;
  margin-bottom: 10px;
  border-radius: 4px;
  transition: all 0.3s;
}
.log-entry:hover { box-shadow: 0 2px 8px rgba(0,0,0,.1); }

.log-level-debug { border-left-color: #909399; }
.log-level-info  { border-left-color: #67C23A; }
.log-level-warn  { border-left-color: #E6A23C; background: #fdf6ec; }
.log-level-error { border-left-color: #F56C6C; background: #fef0f0; }

.log-header {
  display: flex; align-items: center; gap: 15px;
  margin-bottom: 8px; font-size: 12px;
}
.log-source { display: flex; align-items: center; gap: 5px; color: #606266; }
.log-timestamp { margin-left: auto; color: #909399; }

.log-message { margin: 8px 0; }
.log-message pre {
  margin: 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px; color: #303133;
  white-space: pre-wrap; word-wrap: break-word;
}

.log-entry { cursor: pointer; }
.log-expand-hint { margin-left: auto; color: #C0C4CC; font-size: 12px; }
.log-entry:hover .log-expand-hint { color: #409EFF; }

/* Drawer */
.log-detail-drawer :deep(.el-drawer__body) { padding: 0; overflow: hidden; }

.drawer-content {
  display: flex; flex-direction: column; height: 100vh;
  background: #1e1e1e; color: #d4d4d4;
}

.drawer-header {
  padding: 16px 20px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
  flex-shrink: 0;
}
.drawer-title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.drawer-source { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #9cdcfe; }
.drawer-ts { font-size: 12px; color: #6a9955; margin-left: auto; }
.drawer-actions { display: flex; align-items: center; gap: 8px; }
.drawer-actions :deep(.el-button) { background: #3c3c3c; border-color: #555; color: #d4d4d4; }
.drawer-actions :deep(.el-button:hover) { background: #505050; border-color: #777; }

.drawer-section {
  padding: 16px 20px;
  border-bottom: 1px solid #3c3c3c;
  overflow-y: auto;
  flex: 1;
}
.drawer-section-label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
  color: #6a9955; margin-bottom: 10px;
}

.drawer-message {
  margin: 0;
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Courier New', monospace;
  font-size: 13px; line-height: 1.6;
  color: #d4d4d4;
  white-space: pre-wrap; word-wrap: break-word;
  background: transparent;
}

.extra-value {
  margin: 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 12px; color: #ce9178;
  white-space: pre-wrap; word-wrap: break-word;
  background: transparent;
}

.drawer-nav-hint {
  padding: 10px 20px; text-align: right;
  font-size: 12px; color: #6a9955;
  background: #252526; flex-shrink: 0;
}

.logs-content::-webkit-scrollbar { width: 8px; }
.logs-content::-webkit-scrollbar-track { background: #f5f7fa; border-radius: 4px; }
.logs-content::-webkit-scrollbar-thumb { background: #DCDFE6; border-radius: 4px; }
.logs-content::-webkit-scrollbar-thumb:hover { background: #C0C4CC; }
</style>

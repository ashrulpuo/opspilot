<template>
  <div class="salt-services">

    <!-- Header stats row -->
    <el-card shadow="never" class="stats-header">
      <div class="stats-header-inner">
        <div class="stats-title">
          <el-icon><Coin /></el-icon>
          <span>Services</span>
          <el-tag v-if="!isConnected" type="warning" size="small" effect="plain">SSE offline</el-tag>
          <el-tag v-else type="success" size="small" effect="plain">Live</el-tag>
        </div>
        <div class="stats-pills">
          <span class="pill pill-total">{{ totalServices }} total</span>
          <span class="pill pill-running">{{ runningServices }} running</span>
          <span v-if="stoppedServices" class="pill pill-stopped">{{ stoppedServices }} stopped</span>
          <span v-if="failedServices" class="pill pill-failed">{{ failedServices }} failed</span>
        </div>
        <div class="stats-actions">
          <el-input v-model="searchQuery" placeholder="Search…" clearable size="small" style="width:180px" />
        </div>
      </div>
    </el-card>

    <!-- Alert banner: enabled services that are down -->
    <el-alert
      v-if="alertServices.length"
      :title="`${alertServices.length} service${alertServices.length > 1 ? 's' : ''} need attention`"
      type="error"
      show-icon
      :closable="false"
      class="alert-banner"
    >
      <template #default>
        <span v-for="s in alertServices" :key="s.service_name" class="alert-svc-name">
          <el-tag type="danger" size="small" effect="dark">{{ shortName(s.service_name) }}</el-tag>
        </span>
      </template>
    </el-alert>

    <!-- Web Stack card — grouped by category -->
    <el-card v-if="webDevServices.length" shadow="never" class="webdev-card">
      <template #header>
        <div class="webdev-header">
          <el-icon><Monitor /></el-icon>
          <span>Web Stack</span>
          <el-text type="info" size="small">{{ webDevServices.length }} detected</el-text>
        </div>
      </template>
      <div v-for="(svcs, cat) in webDevByCategory" :key="cat" class="webdev-category">
        <div class="webdev-cat-label">{{ cat }}</div>
        <div class="webdev-grid">
          <div
            v-for="svc in svcs"
            :key="svc.service_name"
            :class="['webdev-item', `webdev-${svc.row.status}`]"
          >
            <div class="webdev-dot" :style="{ background: svc.meta.color }"></div>
            <div class="webdev-body">
              <div class="webdev-label">{{ svc.meta.label }}</div>
              <div class="webdev-svc-name">{{ shortName(svc.service_name) }}</div>
            </div>
            <div class="webdev-status">
              <el-tag :type="statusTagType(svc.row.status)" size="small" effect="dark">
                {{ svc.row.status.toUpperCase() }}
              </el-tag>
              <el-tag
                v-if="svc.row.enabled"
                :type="svc.row.enabled === 'enabled' ? 'success' : 'info'"
                size="small"
                effect="plain"
                class="enabled-tag"
              >{{ svc.row.enabled }}</el-tag>
            </div>
            <div class="webdev-ctrl">
              <el-tooltip content="Start" placement="top">
                <el-button size="small" type="success" circle plain
                  :loading="controlLoading[`${svc.service_name}:start`]"
                  :disabled="svc.row.status === 'running'"
                  @click="controlService(svc.service_name, 'start')"
                ><el-icon><VideoPlay /></el-icon></el-button>
              </el-tooltip>
              <el-tooltip content="Stop" placement="top">
                <el-button size="small" type="warning" circle plain
                  :loading="controlLoading[`${svc.service_name}:stop`]"
                  :disabled="svc.row.status === 'stopped'"
                  @click="controlService(svc.service_name, 'stop')"
                ><el-icon><VideoPause /></el-icon></el-button>
              </el-tooltip>
              <el-tooltip content="Restart" placement="top">
                <el-button size="small" type="primary" circle plain
                  :loading="controlLoading[`${svc.service_name}:restart`]"
                  @click="controlService(svc.service_name, 'restart')"
                ><el-icon><RefreshRight /></el-icon></el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Filter tabs + table -->
    <el-card shadow="never" class="table-card">
      <el-tabs v-model="activeTab" class="filter-tabs">
        <el-tab-pane label="All" name="all" />
        <el-tab-pane name="running">
          <template #label><span>Running <el-badge :value="runningServices" type="success" /></span></template>
        </el-tab-pane>
        <el-tab-pane name="stopped">
          <template #label>
            <span>Stopped <el-badge v-if="stoppedServices" :value="stoppedServices" type="warning" /></span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="failed">
          <template #label>
            <span>Failed <el-badge v-if="failedServices" :value="failedServices" type="danger" /></span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <el-table
        :data="filteredServices"
        stripe
        style="width:100%"
        :row-class-name="rowClass"
        empty-text="No services"
      >
        <el-table-column label="Service" min-width="220">
          <template #default="{ row }">
            <div class="svc-name-cell">
              <el-icon class="svc-icon"><Coin /></el-icon>
              <div>
                <div class="svc-name">{{ shortName(row.service_name) }}</div>
                <div v-if="row.description" class="svc-desc">{{ row.description }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="Status" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="dark" size="small">
              {{ row.status.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="Sub-state" width="100">
          <template #default="{ row }">
            <span v-if="row.sub_state" class="sub-state">{{ row.sub_state }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="Autostart" width="110">
          <template #default="{ row }">
            <el-tag
              v-if="row.enabled"
              :type="row.enabled === 'enabled' ? 'success' : row.enabled === 'disabled' ? 'info' : 'warning'"
              size="small"
              effect="plain"
            >{{ row.enabled }}</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>

        <el-table-column label="Uptime" width="120">
          <template #default="{ row }">
            <span :class="['uptime-badge', `uptime-${row.status}`]">
              {{ formatUptime(row.status_changed_at, row.status) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="Last Seen" width="120">
          <template #default="{ row }">
            <span class="last-seen">{{ formatLastSeen(row.last_checked) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="150" align="right">
          <template #default="{ row }">
            <div class="svc-actions">
              <el-tooltip content="Start" placement="top">
                <el-button
                  size="small" type="success" circle plain
                  :loading="controlLoading[`${row.service_name}:start`]"
                  :disabled="row.status === 'running'"
                  @click="controlService(row.service_name, 'start')"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="Stop" placement="top">
                <el-button
                  size="small" type="warning" circle plain
                  :loading="controlLoading[`${row.service_name}:stop`]"
                  :disabled="row.status === 'stopped'"
                  @click="controlService(row.service_name, 'stop')"
                >
                  <el-icon><VideoPause /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="Restart" placement="top">
                <el-button
                  size="small" type="primary" circle plain
                  :loading="controlLoading[`${row.service_name}:restart`]"
                  @click="controlService(row.service_name, 'restart')"
                >
                  <el-icon><RefreshRight /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Coin, Monitor, VideoPlay, VideoPause, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useSaltStream } from '@/composables/useSaltStream'
import request from '@/api/opspilot/client'

const props = defineProps<{ serverId: string }>()

const { services, isConnected } = useSaltStream(props.serverId)

const searchQuery = ref('')
const activeTab = ref('all')

// ── Web Dev service map ───────────────────────────────────────────────────────
interface WebMeta { label: string; category: string; color: string }

const WEB_DEV_MAP: Record<string, WebMeta> = {
  'nginx.service':           { label: 'Nginx',         category: 'Web Server',    color: '#009639' },
  'apache2.service':         { label: 'Apache',        category: 'Web Server',    color: '#D22128' },
  'httpd.service':           { label: 'Apache',        category: 'Web Server',    color: '#D22128' },
  'lighttpd.service':        { label: 'Lighttpd',      category: 'Web Server',    color: '#4C5B6B' },
  'caddy.service':           { label: 'Caddy',         category: 'Web Server',    color: '#00ACD7' },
  'traefik.service':         { label: 'Traefik',       category: 'Proxy',         color: '#24A1C1' },
  'haproxy.service':         { label: 'HAProxy',       category: 'Load Balancer', color: '#106DA9' },
  'varnish.service':         { label: 'Varnish',       category: 'Cache Proxy',   color: '#4591C4' },
  'mysql.service':           { label: 'MySQL',         category: 'Database',      color: '#4479A1' },
  'mysqld.service':          { label: 'MySQL',         category: 'Database',      color: '#4479A1' },
  'mariadb.service':         { label: 'MariaDB',       category: 'Database',      color: '#C0765A' },
  'postgresql.service':      { label: 'PostgreSQL',    category: 'Database',      color: '#336791' },
  'mongod.service':          { label: 'MongoDB',       category: 'Database',      color: '#47A248' },
  'mongodb.service':         { label: 'MongoDB',       category: 'Database',      color: '#47A248' },
  'redis.service':           { label: 'Redis',         category: 'Cache',         color: '#DC382D' },
  'redis-server.service':    { label: 'Redis',         category: 'Cache',         color: '#DC382D' },
  'memcached.service':       { label: 'Memcached',     category: 'Cache',         color: '#666666' },
  'rabbitmq-server.service': { label: 'RabbitMQ',      category: 'Queue',         color: '#FF6600' },
  'elasticsearch.service':   { label: 'Elasticsearch', category: 'Search',        color: '#FEC514' },
  'opensearch.service':      { label: 'OpenSearch',    category: 'Search',        color: '#005EB8' },
  'php-fpm.service':         { label: 'PHP-FPM',       category: 'PHP',           color: '#777BB4' },
  'gunicorn.service':        { label: 'Gunicorn',      category: 'App Server',    color: '#499848' },
  'uwsgi.service':           { label: 'uWSGI',         category: 'App Server',    color: '#555555' },
  'supervisor.service':      { label: 'Supervisor',    category: 'Process Mgr',   color: '#333333' },
  'supervisord.service':     { label: 'Supervisor',    category: 'Process Mgr',   color: '#333333' },
  'postfix.service':         { label: 'Postfix',       category: 'Mail',          color: '#EE0000' },
  'dovecot.service':         { label: 'Dovecot',       category: 'Mail',          color: '#4455AA' },
}

// ── Service list ──────────────────────────────────────────────────────────────
const STATUS_ORDER: Record<string, number> = { failed: 0, stopped: 1, unknown: 2, running: 3 }

const serviceList = computed(() => {
  const svcs = services.value
  if (!svcs || typeof svcs !== 'object') return []
  return Object.values(svcs).filter((s: any) => s.server_id === props.serverId)
})

const sortedServices = computed(() =>
  [...serviceList.value].sort((a: any, b: any) => {
    const sd = (STATUS_ORDER[a.status] ?? 4) - (STATUS_ORDER[b.status] ?? 4)
    return sd !== 0 ? sd : String(a.service_name).localeCompare(String(b.service_name))
  })
)

const filteredServices = computed(() => {
  let list = sortedServices.value
  if (activeTab.value !== 'all') list = list.filter((s: any) => s.status === activeTab.value)
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter((s: any) =>
    s.service_name?.toLowerCase().includes(q) || s.description?.toLowerCase().includes(q)
  )
  return list
})

const totalServices   = computed(() => serviceList.value.length)
const runningServices = computed(() => serviceList.value.filter((s: any) => s.status === 'running').length)
const stoppedServices = computed(() => serviceList.value.filter((s: any) => s.status === 'stopped').length)
const failedServices  = computed(() => serviceList.value.filter((s: any) => s.status === 'failed').length)

// enabled services that are stopped or failed = needs attention
const alertServices = computed(() =>
  serviceList.value.filter((s: any) =>
    s.enabled === 'enabled' && (s.status === 'stopped' || s.status === 'failed')
  )
)

// Web Dev spotlight
const webDevServices = computed(() => {
  const results: { service_name: string; row: any; meta: WebMeta }[] = []
  for (const row of serviceList.value as any[]) {
    const name: string = row.service_name ?? ''
    let meta = WEB_DEV_MAP[name]
    if (!meta && /^php\d/.test(name) && name.includes('fpm')) {
      meta = { label: 'PHP-FPM', category: 'PHP', color: '#777BB4' }
    }
    if (meta) results.push({ service_name: name, row, meta })
  }
  return results.sort((a, b) => (STATUS_ORDER[a.row.status] ?? 4) - (STATUS_ORDER[b.row.status] ?? 4))
})

const CATEGORY_ORDER = ['Web Server', 'Proxy', 'Load Balancer', 'Cache Proxy', 'Database', 'Cache', 'Queue', 'Search', 'PHP', 'App Server', 'Process Mgr', 'Mail']

const webDevByCategory = computed(() => {
  const map: Record<string, typeof webDevServices.value> = {}
  for (const svc of webDevServices.value) {
    const cat = svc.meta.category
    if (!map[cat]) map[cat] = []
    map[cat].push(svc)
  }
  const ordered: Record<string, typeof webDevServices.value> = {}
  for (const cat of CATEGORY_ORDER) {
    if (map[cat]) ordered[cat] = map[cat]
  }
  for (const cat of Object.keys(map)) {
    if (!ordered[cat]) ordered[cat] = map[cat]
  }
  return ordered
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const shortName = (name: string) => name?.replace(/\.service$/, '') ?? name

const statusTagType = (status: string) => {
  if (status === 'running') return 'success'
  if (status === 'failed')  return 'danger'
  if (status === 'stopped') return 'warning'
  return 'info'
}

const rowClass = ({ row }: { row: any }) => {
  if (row.status === 'failed') return 'row-failed'
  if (row.status === 'stopped' && row.enabled === 'enabled') return 'row-alert'
  return ''
}

const normalizeUtc = (ts: string) =>
  ts.endsWith('Z') || ts.includes('+') ? ts : ts + 'Z'

const formatLastSeen = (ts: string) => {
  if (!ts) return '—'
  const diff = Date.now() - new Date(normalizeUtc(ts)).getTime()
  if (diff < 60_000)     return 'just now'
  if (diff < 3_600_000)  return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return `${Math.floor(diff / 86_400_000)}d ago`
}

const formatUptime = (ts: string | undefined, status: string) => {
  if (!ts) return '—'
  const diff = Date.now() - new Date(normalizeUtc(ts)).getTime()
  const label = status === 'running' ? 'up' : 'down'
  if (diff < 60_000)     return `${label} <1m`
  if (diff < 3_600_000)  return `${label} ${Math.floor(diff / 60_000)}m`
  if (diff < 86_400_000) return `${label} ${Math.floor(diff / 3_600_000)}h`
  const days = Math.floor(diff / 86_400_000)
  const hrs  = Math.floor((diff % 86_400_000) / 3_600_000)
  return hrs ? `${label} ${days}d ${hrs}h` : `${label} ${days}d`
}

// ── Service control ───────────────────────────────────────────────────────────
const controlLoading = ref<Record<string, boolean>>({})

const controlService = async (serviceName: string, action: 'start' | 'stop' | 'restart') => {
  const key = `${serviceName}:${action}`
  controlLoading.value[key] = true
  try {
    await request.post(
      `/v1/servers/${props.serverId}/services/${encodeURIComponent(serviceName)}/control`,
      null,
      { params: { action } }
    )
    ElMessage.success(`${action} sent to ${serviceName.replace(/\.service$/, '')}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail ?? `Failed to ${action} service`)
  } finally {
    controlLoading.value[key] = false
  }
}
</script>

<style scoped>
.salt-services { padding: 20px; display: flex; flex-direction: column; gap: 16px; }

.stats-header-inner { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.stats-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; }
.stats-pills { display: flex; gap: 8px; flex-wrap: wrap; flex: 1; }
.pill { padding: 2px 10px; border-radius: 12px; font-size: 13px; font-weight: 500; }
.pill-total   { background: #f4f4f5; color: #606266; }
.pill-running { background: #f0f9eb; color: #67C23A; }
.pill-stopped { background: #fdf6ec; color: #E6A23C; }
.pill-failed  { background: #fef0f0; color: #F56C6C; }

.alert-banner { border-radius: 8px; }
.alert-svc-name { margin-right: 6px; }

.webdev-header { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.webdev-category { margin-bottom: 16px; }
.webdev-category:last-child { margin-bottom: 0; }
.webdev-cat-label {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: #909399; margin-bottom: 8px;
}
.webdev-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 10px;
}
.webdev-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  border: 1px solid #ebeef5; background: #fafafa;
}
.webdev-item.webdev-failed  { border-color: #fab6b6; background: #fff5f5; }
.webdev-item.webdev-stopped { border-color: #f5d98f; background: #fffdf5; }
.webdev-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.webdev-body { flex: 1; min-width: 0; }
.webdev-label { font-weight: 600; font-size: 13px; color: #303133; }
.webdev-svc-name { font-size: 11px; color: #909399; }
.webdev-status { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.webdev-ctrl { display: flex; gap: 4px; }
.enabled-tag { margin-top: 2px; }
.svc-actions { display: flex; gap: 4px; justify-content: flex-end; }

.filter-tabs { margin-bottom: 8px; }
.svc-name-cell { display: flex; align-items: flex-start; gap: 8px; }
.svc-icon { margin-top: 3px; color: #909399; flex-shrink: 0; }
.svc-name { font-weight: 500; font-size: 13px; color: #303133; }
.svc-desc {
  font-size: 11px; color: #909399; margin-top: 2px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px;
}
.sub-state { font-size: 12px; color: #606266; font-family: monospace; }
.last-seen { font-size: 12px; color: #909399; }
.uptime-badge { font-size: 12px; font-weight: 500; }
.uptime-running { color: #67C23A; }
.uptime-stopped { color: #E6A23C; }
.uptime-failed  { color: #F56C6C; }
.uptime-unknown { color: #909399; }
.text-muted { color: #c0c4cc; }

:deep(.row-failed td) { background-color: #fff5f5 !important; }
:deep(.row-alert td)  { background-color: #fffdf0 !important; }
</style>

<template>
  <div class="salt-info">
    <!-- Header -->
    <div class="salt-info-header">
      <el-card shadow="never">
        <el-row :gutter="20">
          <el-col :span="16">
            <div class="salt-info-title">
              <el-icon><Coin /></el-icon>
              <h3>Agent Information</h3>
            </div>
          </el-col>
          <el-col :span="8" class="text-right">
            <el-button type="primary" :icon="RefreshLeft" :loading="refreshing" @click="refreshGrains">
              Refresh Grains
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- Minion Status -->
    <el-row :gutter="20" class="salt-info-stats">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon :size="30"><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Minion Status</div>
              <div :class="['stat-value', minionStatusClass]">
                {{ minionStatus }}
              </div>
              <div class="stat-time">Last seen: {{ formatLastSeen(minion.last_seen) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon :size="30"><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Uptime</div>
              <div class="stat-value">
                {{ formatUptime(server.uptime_seconds) }}
              </div>
              <div class="stat-time">Live from agent metrics</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon :size="30"><Operation /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Facts Synced</div>
              <div class="stat-value">
                {{ formatLastSeen(hostInfo.facts_synced_at) }}
              </div>
              <div class="stat-time">
                {{ hostInfo.facts_synced_at ? formatDateTime(hostInfo.facts_synced_at) : 'Redeploy agent to sync' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Grains Data -->
    <el-row :gutter="20">
      <!-- System Information -->
      <el-col :span="12">
        <el-card shadow="never" header="System Information">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="OS Family">
              <el-tag type="info">{{ grains.os_family }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="OS Name">
              {{ grains.osfullname }}
            </el-descriptions-item>
            <el-descriptions-item label="OS Release">
              {{ grains.osrelease }}
            </el-descriptions-item>
            <el-descriptions-item label="Kernel">
              <code>{{ grains.kernel }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="Architecture">
              <el-tag>{{ grains.osarch }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Hostname">
              <el-tag type="success">{{ grains.hostname }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="FQDN">
              {{ grains.fqdn || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Domain">
              {{ grains.domain || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Virtual">
              <el-tag :type="grains.virtual ? 'warning' : 'success'">
                {{ grains.virtual ? 'Yes' : 'No' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Timezone">
              <code>{{ grains.timezone || 'UTC' }}</code>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- Hardware Information -->
      <el-col :span="12">
        <el-card shadow="never" header="Hardware Information">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="CPU Model">
              {{ grains.cpu_model || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="CPU Cores">
              <el-tag type="info">{{ grains.num_cpus }} cores</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="CPU Architecture">
              {{ grains.cpuarch || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Total Memory">
              {{ formatMemory(grains.mem_total) }}
            </el-descriptions-item>
            <el-descriptions-item label="Virtualized">
              <el-tag :type="grains.virtual ? 'warning' : 'success'">
                {{ grains.virtual ? (grains.virtual_type || 'Yes') : 'Bare Metal' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Cloud Provider">
              <el-tag v-if="grains.cloud_provider && grains.cloud_provider !== 'unknown'" type="info">
                {{ grains.cloud_provider.toUpperCase() }}
              </el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="Region">
              {{ grains.cloud_region || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Instance Type">
              <code v-if="grains.cloud_instance_type">{{ grains.cloud_instance_type }}</code>
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- Storage & Network -->
    <el-row :gutter="20">
      <!-- Storage Information -->
      <el-col :span="12">
        <el-card shadow="never" header="Storage Information">
          <el-empty v-if="storage.filesystems.length === 0" description="No disk data yet — metrics not received" :image-size="60" />
          <el-collapse v-else v-model="storageExpanded">
            <el-collapse-item name="2" title="Filesystems">
              <el-table :data="storage.filesystems" stripe>
                <el-table-column prop="mountpoint" label="Mount Point" />
                <el-table-column prop="fstype" label="Type" width="100">
                  <template #default="{ row }">
                    <el-tag>{{ row.fstype || '-' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="Usage" width="150">
                  <template #default="{ row }">
                    <el-progress
                      :percentage="row.used_percent"
                      :color="getUsageColor(row.used_percent)"
                      :show-text="false"
                    />
                    <span class="usage-text">{{ row.used_percent }}%</span>
                  </template>
                </el-table-column>
                <el-table-column prop="total" label="Total" width="150">
                  <template #default="{ row }">
                    {{ formatBytes(row.total) }}
                  </template>
                </el-table-column>
                <el-table-column prop="used" label="Used" width="150">
                  <template #default="{ row }">
                    {{ formatBytes(row.used) }}
                  </template>
                </el-table-column>
                <el-table-column prop="available" label="Available" width="150">
                  <template #default="{ row }">
                    {{ formatBytes(row.available) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- Network Information -->
      <el-col :span="12">
        <el-card shadow="never" header="Network Information">
          <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
            <el-descriptions-item label="Primary IP">
              <el-tag type="success">{{ hostInfo.ip_address || (serverStore.servers[props.serverId] as any)?.ip_address || '-' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Hostname">
              {{ hostInfo.hostname || '-' }}
            </el-descriptions-item>
          </el-descriptions>
          <el-empty v-if="sortedInterfaces.length === 0" description="Interface detail not yet available — redeploy agent" :image-size="60" />
          <el-collapse v-else v-model="networkExpanded">
            <el-collapse-item v-for="row in sortedInterfaces" :key="row.iface" :name="row.iface">
              <template #title>
                <span style="font-weight:600;margin-right:8px">{{ row.iface }}</span>
                <el-tag v-if="!row.is_up" size="small" type="danger">Down</el-tag>
                <el-tag v-else size="small" type="success">Up</el-tag>
              </template>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="MAC Address">
                  <code>{{ row.mac || '-' }}</code>
                </el-descriptions-item>
                <el-descriptions-item label="IPv4 Address">
                  <el-tag v-if="row.ipv4">{{ row.ipv4 }}/{{ row.ipv4_prefix }}</el-tag>
                  <span v-else>-</span>
                </el-descriptions-item>
                <el-descriptions-item label="IPv6 Address">
                  <el-tag v-if="row.ipv6" type="info">{{ row.ipv6 }}/{{ row.ipv6_prefix }}</el-tag>
                  <span v-else>-</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshLeft, Coin, Connection, Clock, Operation } from '@element-plus/icons-vue'

import { ServersAPI } from '@/api/opspilot/servers'
import { useSaltStream } from '@/composables/useSaltStream'
import { useServerStore } from '@/stores/server'
import { mountpointFromDiskMetric } from '@/utils/dashboardMetrics'

const props = defineProps<{ serverId: string }>()

const { metrics } = useSaltStream(props.serverId)
const serverStore = useServerStore()
const hostInfo = ref<Record<string, any>>({})
const refreshing = ref(false)
const storageExpanded = ref(['2'])
const networkExpanded = ref<string[]>([])

const load = async () => {
  try {
    hostInfo.value = await ServersAPI.getHostInfo(props.serverId)
    const ifaces: string[] = (hostInfo.value.network_interfaces ?? []).map((i: any) => i.iface)
    networkExpanded.value = ifaces.slice(0, 2)
  } catch (e) {
    console.warn('[SaltInfo] host-info fetch failed', e)
  }
}

onMounted(load)

const refreshGrains = async () => {
  refreshing.value = true
  try {
    await load()
    ElMessage.success('Host info refreshed')
  } catch {
    ElMessage.error('Refresh failed')
  } finally {
    refreshing.value = false
  }
}

// ── Agent status ──────────────────────────────────────────────────────────────

// Use latest SSE metric timestamp as the freshest "last seen" signal.
// Falls back to agent_last_seen_at from the server store (set at list-fetch time).
const lastAgentSeenMs = computed(() => {
  const sseTs = Object.values(metrics.value)
    .map(m => m.timestamp ? new Date(m.timestamp).getTime() : 0)
    .reduce((a, b) => Math.max(a, b), 0)
  if (sseTs > 0) return sseTs
  const stored = (serverStore.servers[props.serverId] as any)?.agent_last_seen_at
  return stored ? new Date(stored).getTime() : null
})

const minion = computed(() => ({
  last_seen: lastAgentSeenMs.value ? new Date(lastAgentSeenMs.value).toISOString() : null,
  last_highstate: null,
}))

const minionStatus = computed(() => {
  const ms = lastAgentSeenMs.value
  if (!ms) return 'Unknown'
  const diff = Date.now() - ms
  if (diff < 60_000) return 'Online'
  if (diff < 300_000) return 'Warning'
  return 'Offline'
})

const minionStatusClass = computed(() =>
  ({ Online: 'status-online', Warning: 'status-warning', Offline: 'status-offline' }[minionStatus.value] ?? 'status-unknown')
)

// ── Uptime from SSE ───────────────────────────────────────────────────────────

const server = computed(() => {
  const v = metrics.value['uptime_seconds']?.metric_value
  return { uptime_seconds: (v != null && Number.isFinite(v)) ? v : 0 }
})

// ── Grains shim ───────────────────────────────────────────────────────────────

const grains = computed(() => ({
  os_family:           hostInfo.value.os_name ?? '-',
  osfullname:          [hostInfo.value.os_name, hostInfo.value.os_version].filter(Boolean).join(' ') || '-',
  osrelease:           hostInfo.value.os_version ?? '-',
  kernel:              hostInfo.value.kernel ?? '-',
  osarch:              hostInfo.value.architecture ?? '-',
  hostname:            hostInfo.value.hostname ?? '-',
  fqdn:                hostInfo.value.fqdn ?? '-',
  domain:              hostInfo.value.domain ?? '-',
  virtual:             hostInfo.value.virtual ?? false,
  virtual_type:        hostInfo.value.virtual_type ?? '',
  timezone:            hostInfo.value.timezone ?? 'UTC',
  cpu_model:           hostInfo.value.cpu_model ?? '-',
  num_cpus:            hostInfo.value.cpu_cores ?? '-',
  cpuarch:             hostInfo.value.architecture ?? '-',
  mem_total:           hostInfo.value.memory_mb ? hostInfo.value.memory_mb * 1024 * 1024 : 0,
  cloud_provider:      hostInfo.value.cloud_provider ?? '',
  cloud_region:        hostInfo.value.cloud_region ?? '',
  cloud_instance_type: hostInfo.value.cloud_instance_type ?? '',
}))

const sortedInterfaces = computed(() =>
  [...(hostInfo.value.network_interfaces ?? [])].sort((a: any, b: any) =>
    String(a.iface).localeCompare(String(b.iface))
  )
)

const diskMounts = computed(() => {
  const disks: any[] = []
  for (const metric of Object.values(metrics.value)) {
    const name = metric.metric_name
    if (!name?.startsWith('disk_usage_')) continue
    if (name === 'disk_usage_percent' || name === 'disk_usage') continue
    const mountpoint = mountpointFromDiskMetric(name)
    const meta = (metric.metadata ?? {}) as Record<string, unknown>
    disks.push({
      mountpoint,
      used: typeof meta.used_bytes === 'number' ? meta.used_bytes : 0,
      total: typeof meta.total_bytes === 'number' ? meta.total_bytes : 0,
      used_percent: Math.min(100, metric.metric_value ?? 0),
      fstype: typeof meta.fstype === 'string' ? meta.fstype : '',
      device: typeof meta.device === 'string' ? meta.device : '',
    })
  }
  if (disks.length === 0) {
    const d = metrics.value['disk_usage_percent'] ?? metrics.value['disk_usage']
    if (d) disks.push({ mountpoint: '/', used: 0, total: 0, used_percent: d.metric_value ?? 0, fstype: '', device: '' })
  }
  return disks
})

const storage = computed(() => ({ disks: diskMounts.value, filesystems: diskMounts.value }))

// ── Helpers ───────────────────────────────────────────────────────────────────

const formatLastSeen = (ts: string | undefined) => {
  if (!ts) return 'Never'
  const diff = Date.now() - new Date(ts).getTime()
  if (diff < 60_000) return 'Just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return `${Math.floor(diff / 86_400_000)}d ago`
}

const formatUptime = (seconds: number) => {
  if (!seconds) return 'Unknown'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return [d && `${d}d`, (h || d) && `${h}h`, `${m}m`].filter(Boolean).join(' ') || '0m'
}

const formatMemory = (bytes: number) => {
  if (!bytes) return '-'
  const gb = bytes / 1024 ** 3
  return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / 1024 ** 2).toFixed(0)} MB`
}

const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = bytes, i = 0
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(1)} ${units[i]}`
}

const formatDateTime = (ts: string | undefined) => ts ? new Date(ts).toLocaleString() : '-'
const formatLastHighstate = (_: string | undefined) => 'N/A'

const getUsageColor = (pct: number) =>
  pct < 50 ? '#67C23A' : pct < 70 ? '#E6A23C' : pct < 85 ? '#F59E0B' : '#F56C6C'
</script>

<style scoped>
.salt-info {
  padding: 20px;
}

.salt-info-header {
  margin-bottom: 20px;
}

.salt-info-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.salt-info-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.salt-info-stats {
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
  background: #f5f7fa;
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
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.stat-value.status-online {
  color: #67c23a;
}

.stat-value.status-warning {
  color: #e6a23c;
}

.stat-value.status-offline {
  color: #909399;
}

.stat-time {
  font-size: 12px;
  color: #909399;
}

code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.usage-text {
  margin-left: 10px;
  font-weight: 500;
  font-size: 13px;
}
</style>

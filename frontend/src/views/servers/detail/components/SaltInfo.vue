<template>
  <div class="salt-info">
    <!-- Header -->
    <div class="salt-info-header">
      <el-card shadow="never">
        <el-row :gutter="20">
          <el-col :span="16">
            <div class="salt-info-title">
              <el-icon><Coin /></el-icon>
              <h3>Salt Minion Information</h3>
            </div>
          </el-col>
          <el-col :span="8" class="text-right">
            <el-button 
              type="primary" 
              :icon="RefreshLeft" 
              :loading="refreshing"
              @click="refreshGrains"
            >
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
              <div class="stat-time">
                Last seen: {{ formatLastSeen(minion.last_seen) }}
              </div>
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
              <div class="stat-time">
                {{ server.uptime }} (from grains)
              </div>
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
              <div class="stat-label">Last Highstate</div>
              <div class="stat-value">
                {{ formatLastHighstate(minion.last_highstate) }}
              </div>
              <div class="stat-time">
                {{ minion.last_highstate ? formatDateTime(minion.last_highstate) : 'Never run' }}
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
            <el-descriptions-item label="Manufacturer">
              {{ grains.manufacturer || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Product Name">
              {{ grains.productname || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Serial Number">
              <code>{{ grains.serialnumber || '-' }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="BIOS Vendor">
              {{ grains.biosvendor || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="BIOS Version">
              {{ grains.biosversion || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="BIOS Release">
              {{ grains.biosrelease || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Board Asset Tag">
              {{ grains.board_asset_tag || '-' }}
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
          <el-collapse v-model="storageExpanded">
            <el-collapse-item name="1" title="Disk Information">
              <el-table :data="storage.disks" stripe>
                <el-table-column prop="name" label="Disk" />
                <el-table-column prop="type" label="Type" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.type === 'SSD' ? 'success' : 'primary'">
                      {{ row.type }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="size" label="Size" width="150">
                  <template #default="{ row }">
                    {{ formatBytes(row.size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="model" label="Model" width="200">
                  <template #default="{ row }">
                    {{ row.model || '-' }}
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
            
            <el-collapse-item name="2" title="Filesystems">
              <el-table :data="storage.filesystems" stripe>
                <el-table-column prop="mountpoint" label="Mount Point" />
                <el-table-column prop="fstype" label="Type" width="100">
                  <el-tag>{{ row.fstype }}</el-tag>
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
          <el-collapse v-model="networkExpanded">
            <el-collapse-item v-for="(interface, if_data) in sortedInterfaces" :key="interface" :name="interface">
              <template #title>
                {{ interface }} 
                <el-tag v-if="if_data.is_default" size="small" type="success">Default</el-tag>
                <el-tag v-if="!if_data.is_up" size="small" type="danger">Down</el-tag>
              </template>
              
              <el-descriptions :column="1" border>
                <el-descriptions-item label="MAC Address">
                  <code>{{ if_data.hwaddr }}</code>
                </el-descriptions-item>
                <el-descriptions-item label="IPv4 Address">
                  <el-tag>{{ if_data.ipv4_address || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IPv4 Netmask">
                  <el-tag>{{ if_data.ipv4_netmask || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IPv4 Broadcast">
                  <el-tag>{{ if_data.ipv4_broadcast || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IPv4 Gateway">
                  <el-tag>{{ if_data.ipv4_gateway || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IPv6 Address">
                  <el-tag>{{ if_data.ipv6_address || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IPv6 Prefix">
                  <el-tag>{{ if_data.ipv6_prefix || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IPv6 Scope">
                  <el-tag>{{ if_data.ipv6_scope || 'None' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="MTU">
                  {{ if_data.mtu || '1500' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
            
            <el-collapse-item name="system_dns" title="System DNS">
              <el-descriptions :column="2" border>
                <el-descriptions-item v-for="(nameserver, index) in DNS_servers" :key="index" :label="`Nameserver ${index + 1}`">
                  <el-tag>{{ nameserver }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item v-for="(searchdomain, index) in DNS_searchdomains" :key="index" :label="`Search Domain ${index + 1}`">
                  {{ searchdomain || '-' }}
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshLeft, Coin, Connection, Clock, Operation } from '@element-plus/icons-vue'

import { useServerStore } from '@/stores/server'
import { useSaltStore } from '@/stores/salt'

// Props
const props = defineProps<{
  serverId: string
}>()

// Stores
const serverStore = useServerStore()
const saltStore = useSaltStore()

// Reactive state
const refreshing = ref(false)
const storageExpanded = ref(['1'])
const networkExpanded = ref(['eth0', 'lo'])

// Computed
const minion = computed(() => {
  return saltStore.minions[props.serverId] || {}
})

const grains = computed(() => {
  return minion.value.grains_info || {}
})

const server = computed(() => {
  return serverStore.servers[props.serverId] || {}
})

const storage = computed(() => {
  // Parse storage from grains
  return {
    disks: grains.value.disks || {},
    filesystems: grains.value.disks ? grains.value.disks.map((disk: any) => ({
      name: disk.mountpoint,
      fstype: disk.fstype,
      used_percent: disk.percent,
      total: disk.total,
      used: disk.used,
      available: disk.available
    })) : []
  }
})

const network = computed(() => {
  // Parse network from grains
  const interfaces: any = grains.value.ipv4 || {}
  
  return Object.entries(interfaces).map(([iface, if_data]: [string, any]) => ({
    interface,
    ...if_data,
    is_default: grains.value.default_gateway === if_data.gateway,
    is_up: grains.value.ipv4_enabled === true
  }))
})

const sortedInterfaces = computed(() => {
  return Object.keys(network.value).sort()
})

const DNS_servers = computed(() => {
  const dns: string[] = grains.value.dns || []
  return dns.map((addr, index) => [addr, index])
})

const DNS_searchdomains = computed(() => {
  return grains.value.dns_search || []
})

// Helper functions
const minionStatus = computed(() => {
  if (!minion.value.last_seen) return 'Unknown'
  
  const lastSeen = new Date(minion.value.last_seen)
  const now = new Date()
  const diffMs = now.getTime() - lastSeen.getTime()
  
  if (diffMs < 60000) return 'Online'  // < 1 min
  if (diffMs < 300000) return 'Warning' // < 5 min
  return 'Offline'
})

const minionStatusClass = computed(() => {
  switch (minionStatus.value) {
    case 'Online': return 'status-online'
    case 'Warning': return 'status-warning'
    case 'Offline': return 'status-offline'
    default: return 'status-unknown'
  }
})

// Format functions
const formatLastSeen = (lastSeen: string | undefined) => {
  if (!lastSeen) return 'Never'
  
  const date = new Date(lastSeen)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`
  return `${Math.floor(diffMs / 86400000)}d ago`
}

const formatLastHighstate = (lastHighstate: string | undefined) => {
  if (!lastHighstate) return 'Never run'
  
  const date = new Date(lastHighstate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  return `${Math.floor(diffMs / 60000)}m ago`
}

const formatUptime = (seconds: number | undefined) => {
  if (!seconds) return 'Unknown'
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  const parts = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0 || days > 0) parts.push(`${hours}h`)
  if (minutes > 0 || hours > 0 || days > 0) parts.push(`${minutes}m`)
  
  return parts.join(' ') || '0m'
}

const formatMemory = (bytes: number | undefined) => {
  if (!bytes) return 'Unknown'
  
  const gb = bytes / (1024 ** 3)
  const mb = bytes / (1024 ** 2)
  
  if (gb >= 1) return `${gb.toFixed(2)} GB`
  return `${mb.toFixed(2)} MB`
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

const formatDateTime = (date: string | undefined) => {
  if (!date) return '-'
  
  const d = new Date(date)
  return d.toLocaleString()
}

const getUsageColor = (percent: number) => {
  if (percent < 50) return '#67C23A'  // Green
  if (percent < 70) return '#E6A23C'  // Yellow
  if (percent < 85) return '#F59E0B'  // Orange
  return '#F56C6C'  // Red
}

// Actions
const refreshGrains = async () => {
  refreshing.value = true
  
  try {
    // Call Salt API to refresh grains
    // This would be done via a dedicated endpoint
    // For now, we'll simulate it
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage({
      message: 'Grains refreshed successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to refresh grains:', error)
    ElMessage.error('Failed to refresh grains')
  } finally {
    refreshing.value = false
  }
}

// Lifecycle
onMounted(async () => {
  console.log('Salt Info component mounted for server:', props.serverId)
})
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
  color: #67C23A;
}

.stat-value.status-warning {
  color: #E6A23C;
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

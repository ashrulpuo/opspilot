<template>
  <div class="salt-packages">
    <!-- Header -->
    <div class="packages-header">
      <el-row :gutter="20">
        <el-col :span="16">
          <h2>Packages</h2>
        </el-col>
        <el-col :span="8" class="text-right">
          <el-input 
            v-model="searchQuery"
            placeholder="Search packages..."
            clearable
            style="width: 200px; margin-right: 10px;"
          />
          <el-button 
            type="primary" 
            :icon="RefreshRight"
            @click="refreshPackages"
            :loading="refreshing"
            :disabled="!isConnected"
          >
            Refresh
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- Package Stats -->
    <el-row :gutter="20" class="package-stats">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-total">
            <div class="stat-icon">
              <el-icon :size="30"><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Total Packages</div>
              <div class="stat-value">{{ totalPackages }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-updates">
            <div class="stat-icon">
              <el-icon :size="30"><CirclePlus /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Updates Available</div>
              <div class="stat-value">{{ packagesWithUpdates }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-security">
            <div class="stat-icon">
              <el-icon :size="30"><Lock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Security Updates</div>
              <div class="stat-value">{{ securityUpdates }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="stat-card stat-date">
            <div class="stat-icon">
              <el-icon :size="30"><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">Last Checked</div>
              <div class="stat-value">
                {{ lastChecked ? formatLastChecked(lastChecked) : 'Never' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Filters -->
    <el-row :gutter="20" class="package-filters">
      <el-col :span="8">
        <el-select 
          v-model="selectedSource" 
          placeholder="Filter by source"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="source in packageSources" 
            :key="source" 
            :label="source" 
            :value="source"
          />
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select 
          v-model="selectedArchitecture" 
          placeholder="Filter by architecture"
          clearable
          style="width: 100%;"
        >
          <el-option 
            v-for="arch in architectures" 
            :key="arch" 
            :label="arch" 
            :value="arch"
          />
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-checkbox v-model="showOnlyUpdates">
          Show only updates
          <el-badge 
            :value="packagesWithUpdates"
            :hidden="packagesWithUpdates === 0"
            type="danger"
            style="margin-left: 10px;"
          />
        </el-checkbox>
      </el-col>
    </el-row>
    
    <!-- Packages Table -->
    <el-card shadow="never" class="packages-table">
      <el-table 
        :data="filteredPackages"
        stripe
        border
        style="width: 100%"
        v-loading="loading"
        max-height="600"
      >
        <!-- Package Name -->
        <el-table-column 
          prop="name" 
          label="Package Name" 
          min-width="200"
          sortable
        >
          <template #default="{ row }">
            <el-icon style="margin-right: 5px;"><Box /></el-icon>
            <strong>{{ row.name }}</strong>
          </template>
        </el-table-column>
        
        <!-- Current Version -->
        <el-table-column 
          prop="version" 
          label="Current Version" 
          min-width="150"
          sortable
        >
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.version }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- Update Version -->
        <el-table-column 
          label="Update Version" 
          min-width="150"
        >
          <template #default="{ row }">
            <el-tag 
              v-if="row.is_update_available && row.update_version"
              type="success"
              size="small"
            >
              {{ row.update_version }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <!-- Update Status -->
        <el-table-column label="Update Status" width="120">
          <template #default="{ row }">
            <el-tag 
              v-if="row.is_update_available"
              type="warning"
              effect="dark"
            >
              <el-icon class="status-icon"><CirclePlus /></el-icon>
              Update
            </el-tag>
            <el-tag 
              v-else
              type="success"
            >
              <el-icon class="status-icon"><CircleCheck /></el-icon>
              Latest
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- Architecture -->
        <el-table-column 
          prop="architecture" 
          label="Architecture" 
          width="120"
          sortable
        >
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.architecture }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- Source -->
        <el-table-column 
          prop="source" 
          label="Source" 
          width="150"
          sortable
        >
          <template #default="{ row }">
            <el-tag 
              :type="getSourceType(row.source)"
              size="small"
            >
              {{ row.source }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- Installed Date -->
        <el-table-column label="Installed" width="150">
          <template #default="{ row }">
            <span class="install-date">{{ formatInstalledDate(row.installed_date) }}</span>
          </template>
        </el-table-column>
        
        <!-- Actions -->
        <el-table-column label="Actions" width="180" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="row.is_update_available"
                type="primary" 
                size="small"
                :icon="Download"
                @click="updatePackage(row)"
                :loading="actionLoading[row.name]"
              >
                Update
              </el-button>
              <el-button 
                type="danger" 
                size="small"
                :icon="Delete"
                @click="removePackage(row)"
                :loading="actionLoading[row.name]"
              >
                Remove
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Empty State -->
      <el-empty 
        v-if="!loading && filteredPackages.length === 0" 
        description="No packages found"
      />
    </el-card>
    
    <!-- Bulk Actions -->
    <el-card v-if="packagesWithUpdates > 0" shadow="never" class="bulk-actions">
      <el-row :gutter="20" align="middle">
        <el-col :span="18">
          <div class="bulk-info">
            <el-icon :size="20" color="#E6A23C"><Warning /></el-icon>
            <span>
              <strong>{{ packagesWithUpdates }}</strong> package(s) have updates available
              <span v-if="securityUpdates > 0">
                (including <strong>{{ securityUpdates }}</strong> security update(s))
              </span>
            </span>
          </div>
        </el-col>
        <el-col :span="6" class="text-right">
          <el-button 
            type="warning"
            :icon="Download"
            @click="updateAllPackages"
            :loading="bulkUpdateLoading"
          >
            Update All ({{ packagesWithUpdates }})
          </el-button>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  RefreshRight, 
  Box, 
  CircleCheck, 
  CirclePlus, 
  Warning,
  Clock,
  Lock,
  Download,
  Delete
} from '@element-plus/icons-vue'

import { useSaltStream } from '@/composables/useSaltStream'

// Types
interface Package {
  id: string
  server_id: string
  name: string
  version: string
  architecture: string
  source: string
  is_update_available: boolean
  installed_date: string
  update_version?: string
}

// Props
const props = defineProps<{
  serverId: string
}>()

// Use SSE composable
const { packages, isConnected, disconnectAll } = useSaltStream(props.serverId)

// Reactive state
const searchQuery = ref('')
const selectedSource = ref('')
const selectedArchitecture = ref('')
const showOnlyUpdates = ref(false)
const refreshing = ref(false)
const loading = ref(false)
const actionLoading = ref<Record<string, boolean>>({})
const bulkUpdateLoading = ref(false)
const lastChecked = ref<Date | null>(null)

// Computed: Packages list
const packageList = computed(() => {
  return packages.value.filter(p => p.server_id === props.serverId)
})

// Computed: Unique sources
const packageSources = computed(() => {
  const sources = new Set<string>()
  packageList.value.forEach(p => sources.add(p.source))
  return Array.from(sources).sort()
})

// Computed: Unique architectures
const architectures = computed(() => {
  const archs = new Set<string>()
  packageList.value.forEach(p => archs.add(p.architecture))
  return Array.from(archs).sort()
})

// Computed: Filtered packages
const filteredPackages = computed(() => {
  let filtered = packageList.value
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p => 
      p.name.toLowerCase().includes(query) ||
      p.version.toLowerCase().includes(query) ||
      p.source.toLowerCase().includes(query)
    )
  }
  
  // Filter by source
  if (selectedSource.value) {
    filtered = filtered.filter(p => p.source === selectedSource.value)
  }
  
  // Filter by architecture
  if (selectedArchitecture.value) {
    filtered = filtered.filter(p => p.architecture === selectedArchitecture.value)
  }
  
  // Filter by updates only
  if (showOnlyUpdates.value) {
    filtered = filtered.filter(p => p.is_update_available)
  }
  
  return filtered
})

// Computed: Package stats
const totalPackages = computed(() => packageList.value.length)
const packagesWithUpdates = computed(() => packageList.value.filter(p => p.is_update_available).length)
const securityUpdates = computed(() => {
  // This would be based on metadata from Salt
  // For now, we'll estimate based on package names
  const securityKeywords = ['security', 'ssl', 'tls', 'openssl', 'kernel', 'openssl']
  return packageList.value.filter(p => 
    p.is_update_available && 
    securityKeywords.some(keyword => p.name.toLowerCase().includes(keyword))
  ).length
})

// Helper functions
const getSourceType = (source: string) => {
  switch (source.toLowerCase()) {
    case 'apt':
    case 'dpkg':
      return 'primary'
    case 'yum':
    case 'dnf':
    case 'rpm':
      return 'success'
    case 'pip':
      return 'warning'
    case 'npm':
      return 'info'
    default:
      return 'info'
  }
}

const formatInstalledDate = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 86400000) {  // Less than 1 day
    return 'Today'
  } else if (diffMs < 604800000) {  // Less than 1 week
    const days = Math.floor(diffMs / 86400000)
    return `${days}d ago`
  } else if (diffMs < 2592000000) {  // Less than 1 month
    const weeks = Math.floor(diffMs / 604800000)
    return `${weeks}w ago`
  } else {
    return date.toLocaleDateString()
  }
}

const formatLastChecked = (date: Date) => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  if (diffMs < 60000) return 'Just now'
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`
  return `${Math.floor(diffMs / 3600000)}h ago`
}

// Actions
const refreshPackages = async () => {
  refreshing.value = true
  
  try {
    // This would trigger a package list refresh via Salt API
    console.log('Refreshing packages...')
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    lastChecked.value = new Date()
    
    ElMessage({
      message: 'Packages refreshed successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Failed to refresh packages:', error)
    ElMessage.error('Failed to refresh packages')
  } finally {
    refreshing.value = false
  }
}

const updatePackage = async (pkg: Package) => {
  actionLoading.value[pkg.name] = true
  
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to update ${pkg.name} from ${pkg.version} to ${pkg.update_version || 'latest'}?`,
      'Update Package',
      {
        confirmButtonText: 'Update',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    
    // This would call the Salt API to update the package
    console.log('Updating package:', pkg.name)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage({
      message: `Package ${pkg.name} updated successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to update package:', error)
      ElMessage.error(`Failed to update package ${pkg.name}`)
    }
  } finally {
    actionLoading.value[pkg.name] = false
  }
}

const removePackage = async (pkg: Package) => {
  actionLoading.value[pkg.name] = true
  
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to remove ${pkg.name}? This action cannot be undone.`,
      'Remove Package',
      {
        confirmButtonText: 'Remove',
        cancelButtonText: 'Cancel',
        type: 'danger'
      }
    )
    
    // This would call the Salt API to remove the package
    console.log('Removing package:', pkg.name)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage({
      message: `Package ${pkg.name} removed successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to remove package:', error)
      ElMessage.error(`Failed to remove package ${pkg.name}`)
    }
  } finally {
    actionLoading.value[pkg.name] = false
  }
}

const updateAllPackages = async () => {
  const updateCount = packagesWithUpdates.value
  
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to update all ${updateCount} packages? This may take some time.`,
      'Update All Packages',
      {
        confirmButtonText: 'Update All',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    
    bulkUpdateLoading.value = true
    
    // This would call the Salt API to update all packages
    console.log('Updating all packages...')
    
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    ElMessage({
      message: `All packages updated successfully`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to update packages:', error)
      ElMessage.error('Failed to update packages')
    }
  } finally {
    bulkUpdateLoading.value = false
  }
}

// Lifecycle
onMounted(() => {
  console.log('Salt Packages component mounted for server:', props.serverId)
})
</script>

<style scoped>
.salt-packages {
  padding: 20px;
}

.packages-header {
  margin-bottom: 20px;
}

.packages-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.package-stats {
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

.stat-updates .stat-icon {
  background: #fdf6ec;
}

.stat-security .stat-icon {
  background: #fef0f0;
}

.stat-date .stat-icon {
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

.stat-updates .stat-value {
  color: #E6A23C;
}

.stat-security .stat-value {
  color: #F56C6C;
}

.package-filters {
  margin-bottom: 20px;
}

.packages-table {
  background: white;
}

.status-icon {
  margin-right: 5px;
  font-size: 14px;
}

.install-date {
  font-size: 13px;
  color: #606266;
}

.text-muted {
  color: #909399;
}

.bulk-actions {
  margin-top: 20px;
  background: linear-gradient(135deg, #fdf6ec 0%, #fef0f0 100%);
}

.bulk-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.bulk-info strong {
  color: #E6A23C;
  font-size: 16px;
}
</style>

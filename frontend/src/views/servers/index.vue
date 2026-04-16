<template>
  <div class="servers-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Servers</h1>
        <p class="page-subtitle">Manage your infrastructure</p>
      </div>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        Add Server
      </el-button>
    </div>

    <!-- Organization Selector -->
    <div class="org-selector" v-if="orgStore.organizations.length > 1">
      <el-select v-model="selectedOrgId" placeholder="Select organization" @change="handleOrgChange">
        <el-option v-for="org in orgStore.organizations" :key="org.id" :label="org.name" :value="org.id" />
      </el-select>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-primary">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Total Servers</p>
          <p class="stat-value">{{ serverStore.servers.length }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-success">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Online</p>
          <p class="stat-value">{{ serverStore.onlineServers.length }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-warning">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Offline</p>
          <p class="stat-value">{{ serverStore.offlineServers.length }}</p>
        </div>
      </div>
    </div>

    <!-- Servers Table -->
    <div class="servers-table hc-card">
      <el-table
        :data="serverStore.servers"
        v-loading="serverStore.loading"
        @row-click="handleRowClick"
        style="width: 100%"
      >
        <el-table-column prop="hostname" label="Hostname" min-width="180">
          <template #default="{ row }">
            <div class="server-name-cell">
              <div class="status-dot" :class="`status-${row.status}`" />
              <span class="hostname-text">{{ row.hostname }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" label="IP Address" min-width="140" />

        <el-table-column prop="os_type" label="OS" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getOSType(row.os_type)" size="small">
              {{ row.os_type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="domain_name" label="Domain" min-width="180">
          <template #default="{ row }">
            <span v-if="row.domain_name">{{ row.domain_name }}</span>
            <span v-else class="empty-text">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="web_server_type" label="Web Server" min-width="120">
          <template #default="{ row }">
            <el-tag v-if="row.web_server_type" type="info" size="small">
              {{ row.web_server_type }}
            </el-tag>
            <span v-else class="empty-text">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="Status" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="Last Seen" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="handleSSH(row)">
              <el-icon><Monitor /></el-icon>
              SSH
            </el-button>
            <el-button link type="primary" size="small" @click.stop="handleView(row)">
              <el-icon><View /></el-icon>
              View
            </el-button>
            <el-popconfirm title="Are you sure you want to delete this server?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small" @click.stop>
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!serverStore.loading && serverStore.servers.length === 0"
        description="No servers found. Add your first server to get started."
      />
    </div>

    <!-- Add Server Dialog -->
    <el-dialog v-model="showAddDialog" title="Add New Server" width="600px" :close-on-click-modal="false">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="120px">
        <el-form-item label="Hostname" prop="hostname">
          <el-input v-model="addForm.hostname" placeholder="e.g., web-server-01" :disabled="addLoading" />
        </el-form-item>

        <el-form-item label="IP Address" prop="ip_address">
          <el-input v-model="addForm.ip_address" placeholder="e.g., 192.168.1.100" :disabled="addLoading" />
        </el-form-item>

        <el-form-item label="OS Type" prop="os_type">
          <el-select v-model="addForm.os_type" placeholder="Select OS type" :disabled="addLoading" style="width: 100%">
            <el-option label="Linux" value="linux" />
            <el-option label="macOS" value="macos" />
            <el-option label="Windows" value="windows" />
          </el-select>
        </el-form-item>

        <el-form-item label="Domain Name" prop="domain_name">
          <el-input v-model="addForm.domain_name" placeholder="e.g., example.com (optional)" :disabled="addLoading" />
        </el-form-item>

        <el-form-item label="Web Server" prop="web_server_type">
          <el-select
            v-model="addForm.web_server_type"
            placeholder="Select web server (optional)"
            :disabled="addLoading"
            style="width: 100%"
            clearable
          >
            <el-option label="Nginx" value="nginx" />
            <el-option label="Apache" value="apache" />
            <el-option label="Caddy" value="caddy" />
            <el-option label="IIS" value="iis" />
            <el-option label="None" value="none" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false" :disabled="addLoading"> Cancel </el-button>
        <el-button type="primary" @click="handleAdd" :loading="addLoading"> Add Server </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Monitor, View, Delete, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { useOpsPilotServerStore } from '@/stores/modules/opspilot'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'
import { OrganizationsAPI } from '@/api/opspilot/organizations'

const router = useRouter()
const serverStore = useOpsPilotServerStore()
const orgStore = useOpsPilotOrganizationStore()

const showAddDialog = ref(false)
const addLoading = ref(false)
const addFormRef = ref<FormInstance>()
const selectedOrgId = ref<string>()

const addForm = reactive({
  hostname: '',
  ip_address: '',
  os_type: 'linux' as 'linux' | 'macos' | 'windows',
  domain_name: '',
  web_server_type: '' as string | undefined,
})

const addRules: FormRules = {
  hostname: [
    { required: true, message: 'Please enter hostname', trigger: 'blur' },
    { min: 3, message: 'Hostname must be at least 3 characters', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9-]+$/,
      message: 'Hostname can only contain letters, numbers, and hyphens',
      trigger: 'blur',
    },
  ],
  ip_address: [
    { required: true, message: 'Please enter IP address', trigger: 'blur' },
    {
      pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([a-fA-F0-9:]+)$/,
      message: 'Please enter a valid IP address (IPv4 or IPv6)',
      trigger: 'blur',
    },
  ],
  os_type: [{ required: true, message: 'Please select OS type', trigger: 'change' }],
}

const getOSType = (osType: string) => {
  switch (osType.toLowerCase()) {
    case 'linux':
      return 'primary'
    case 'macos':
      return 'info'
    case 'windows':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'info'
    case 'error':
      return 'danger'
    case 'connecting':
      return 'warning'
    default:
      return 'info'
  }
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

const handleOrgChange = async (orgId: string) => {
  await serverStore.fetchServers(orgId)
}

const handleRowClick = (row: any) => {
  router.push(`/servers/${row.id}`)
}

const handleSSH = (row: any) => {
  router.push(`/servers/${row.id}?tab=ssh`)
}

const handleView = (row: any) => {
  router.push(`/servers/${row.id}`)
}

const handleAdd = async () => {
  if (!addFormRef.value) {
    return
  }

  try {
    const valid = await addFormRef.value.validate()
    if (!valid) {
      return
    }

    const orgId = selectedOrgId.value || orgStore.currentOrganization?.id
    if (!orgId) {
      ElMessage.error('No organization selected')
      return
    }

    addLoading.value = true

    await OrganizationsAPI.createServer(orgId, {
      hostname: addForm.hostname,
      ip_address: addForm.ip_address,
      port: 22,
      ssh_port: 22,
      os_type: addForm.os_type,
      tags: [],
    })

    ElMessage.success('Server added successfully')
    showAddDialog.value = false

    // Reset form
    addFormRef.value.resetFields()

    // Refresh server list
    await serverStore.fetchServers(orgId)
  } catch (error: any) {
    console.error('Add server error:', error)
    ElMessage.error(error.message || 'Failed to add server')
  } finally {
    addLoading.value = false
  }
}

const handleDelete = async (row: any) => {
  try {
    await serverStore.deleteServer(row.id)
    ElMessage.success('Server deleted successfully')
  } catch (error: any) {
    console.error('Delete server error:', error)
    ElMessage.error(error.message || 'Failed to delete server')
  }
}

onMounted(async () => {
  // Fetch organizations
  if (orgStore.organizations.length === 0) {
    await orgStore.fetchOrganizations()
  }

  // Set selected organization
  selectedOrgId.value = orgStore.currentOrganization?.id

  // Fetch servers
  await serverStore.fetchServers(selectedOrgId.value)
})
</script>

<style scoped lang="scss">
.servers-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
    .page-title {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 2rem;
      font-weight: 700;
      color: #000000;
      line-height: 1.2;
      margin: 0 0 4px 0;
    }

    .page-subtitle {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.9375rem;
      font-weight: 400;
      color: #656a76;
      line-height: 1.5;
      margin: 0;
    }
  }
}

html.dark .page-header .header-left {
  .page-title {
    color: #ffffff;
  }

  .page-subtitle {
    color: #d5d7db;
  }
}

.org-selector {
  margin-bottom: 24px;
  max-width: 400px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;

    &.stat-icon-primary {
      background: rgba(21, 24, 30, 0.1);
      color: #15181e;
    }

    &.stat-icon-success {
      background: rgba(20, 198, 203, 0.1);
      color: #14c6cb;
    }

    &.stat-icon-warning {
      background: rgba(187, 90, 0, 0.1);
      color: #bb5a00;
    }
  }

  .stat-content {
    .stat-label {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.8125rem;
      font-weight: 500;
      color: #656a76;
      line-height: 1.4;
      margin: 0 0 4px 0;
    }

    .stat-value {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1.5rem;
      font-weight: 700;
      color: #000000;
      line-height: 1.2;
      margin: 0;
    }
  }
}

html.dark .stat-card {
  .stat-icon {
    &.stat-icon-primary {
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
    }
  }

  .stat-content {
    .stat-label {
      color: #b2b6bd;
    }

    .stat-value {
      color: #ffffff;
    }
  }
}

.servers-table {
  .server-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;

      &.status-online {
        background: #14c6cb;
      }

      &.status-offline {
        background: #656a76;
      }

      &.status-error {
        background: #731e25;
      }

      &.status-connecting {
        background: #bb5a00;
        animation: pulse 1.5s ease-in-out infinite;
      }
    }

    .hostname-text {
      font-weight: 500;
      color: #000000;
    }
  }

  .empty-text {
    color: #656a76;
  }
}

html.dark .servers-table .server-name-cell .hostname-text {
  color: #ffffff;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

// Responsive design
@media (max-width: 768px) {
  .servers-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .header-left {
      .page-title {
        font-size: 1.5rem;
      }
    }
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>

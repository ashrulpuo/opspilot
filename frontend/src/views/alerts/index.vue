<template>
  <div class="alerts-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Alerts</h1>
        <p class="page-subtitle">Monitor and manage alerts across your infrastructure</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        Create Alert
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
          <el-icon><Bell /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Total Alerts</p>
          <p class="stat-value">{{ alertStore.stats?.total || 0 }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-warning">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Active</p>
          <p class="stat-value">{{ alertStore.stats?.active || 0 }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-critical">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Critical</p>
          <p class="stat-value">{{ alertStore.stats?.critical || 0 }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-success">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Resolved</p>
          <p class="stat-value">{{ alertStore.stats?.resolved || 0 }}</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section hc-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="Severity">
          <el-select v-model="filters.severity" placeholder="All" clearable @change="handleFilterChange">
            <el-option label="Critical" value="critical" />
            <el-option label="Warning" value="warning" />
            <el-option label="Info" value="info" />
          </el-select>
        </el-form-item>

        <el-form-item label="Status">
          <el-select v-model="filters.resolved" placeholder="All" clearable @change="handleFilterChange">
            <el-option label="Active" :value="false" />
            <el-option label="Resolved" :value="true" />
          </el-select>
        </el-form-item>

        <el-form-item label="Server">
          <el-select v-model="filters.server_id" placeholder="All" clearable filterable @change="handleFilterChange">
            <el-option
              v-for="server in serverStore.servers"
              :key="server.id"
              :label="server.hostname"
              :value="server.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Date Range">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            placeholder="Select range"
            @change="handleDateRangeChange"
          />
        </el-form-item>

        <el-form-item>
          <el-button @click="resetFilters">Reset</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Alerts Table -->
    <div class="alerts-table hc-card">
      <el-table :data="alertStore.alerts" v-loading="alertStore.loading" style="width: 100%">
        <el-table-column prop="severity" label="Severity" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ row.severity.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="Title" min-width="200" />

        <el-table-column prop="message" label="Message" min-width="300" show-overflow-tooltip />

        <el-table-column prop="server_hostname" label="Server" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToServer(row.server_id)">
              {{ row.server_hostname || 'Unknown' }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="Type" width="100">
          <template #default="{ row }">
            {{ row.type.toUpperCase() }}
          </template>
        </el-table-column>

        <el-table-column prop="resolved" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="row.resolved ? 'success' : 'warning'" size="small">
              {{ row.resolved ? 'Resolved' : 'Active' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="Created" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="!row.resolved" link type="primary" size="small" @click="handleResolve(row)">
              <el-icon><CircleCheck /></el-icon>
              Resolve
            </el-button>
            <el-button link type="primary" size="small" @click="handleView(row)">
              <el-icon><View /></el-icon>
              View
            </el-button>
            <el-popconfirm title="Are you sure you want to delete this alert?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!alertStore.loading && alertStore.alerts.length === 0" description="No alerts found" />
    </div>

    <!-- Create Alert Dialog -->
    <el-dialog v-model="showCreateDialog" title="Create Alert" width="600px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="Server" prop="server_id">
          <el-select v-model="createForm.server_id" placeholder="Select server" style="width: 100%">
            <el-option
              v-for="server in serverStore.servers"
              :key="server.id"
              :label="server.hostname"
              :value="server.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Type" prop="type">
          <el-select v-model="createForm.type" placeholder="Select type" style="width: 100%">
            <el-option label="CPU" value="cpu" />
            <el-option label="Memory" value="memory" />
            <el-option label="Disk" value="disk" />
            <el-option label="Network" value="network" />
            <el-option label="Service" value="service" />
            <el-option label="System" value="system" />
          </el-select>
        </el-form-item>

        <el-form-item label="Severity" prop="severity">
          <el-select v-model="createForm.severity" placeholder="Select severity" style="width: 100%">
            <el-option label="Critical" value="critical" />
            <el-option label="Warning" value="warning" />
            <el-option label="Info" value="info" />
          </el-select>
        </el-form-item>

        <el-form-item label="Title" prop="title">
          <el-input v-model="createForm.title" placeholder="Alert title" />
        </el-form-item>

        <el-form-item label="Message" prop="message">
          <el-input v-model="createForm.message" type="textarea" :rows="4" placeholder="Alert message" />
        </el-form-item>

        <el-form-item label="Threshold">
          <el-input-number
            v-model="createForm.threshold"
            :min="0"
            :max="100"
            placeholder="Optional"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createLoading"> Create Alert </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Bell, Warning, CircleClose, CircleCheck, View, Delete } from '@element-plus/icons-vue'
import { useOpsPilotAlertStore } from '@/stores/modules/opspilot'
import { useOpsPilotServerStore } from '@/stores/modules/opspilot'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'

const router = useRouter()
const alertStore = useOpsPilotAlertStore()
const serverStore = useOpsPilotServerStore()
const orgStore = useOpsPilotOrganizationStore()

const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const selectedOrgId = ref<string>()
const dateRange = ref<[Date, Date] | null>(null)

const createForm = reactive({
  server_id: '',
  type: 'cpu',
  severity: 'warning',
  title: '',
  message: '',
  threshold: undefined as number | undefined,
})

const filters = reactive({
  severity: undefined as string | undefined,
  resolved: undefined as boolean | undefined,
  server_id: undefined as string | undefined,
})

const createRules: FormRules = {
  server_id: [{ required: true, message: 'Please select a server', trigger: 'change' }],
  type: [{ required: true, message: 'Please select a type', trigger: 'change' }],
  severity: [{ required: true, message: 'Please select a severity', trigger: 'change' }],
  title: [{ required: true, message: 'Please enter a title', trigger: 'blur' }],
  message: [{ required: true, message: 'Please enter a message', trigger: 'blur' }],
}

const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    default:
      return 'info'
  }
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const handleOrgChange = async (orgId: string) => {
  await serverStore.fetchServers(orgId)
  await alertStore.fetchStats()
  await alertStore.fetchAlerts({ organization_id: orgId })
}

const handleFilterChange = async () => {
  const params: any = {}
  if (filters.severity) params.severity = filters.severity
  if (filters.resolved !== undefined) params.resolved = filters.resolved
  if (filters.server_id) params.server_id = filters.server_id

  await alertStore.fetchAlerts(params)
}

const handleDateRangeChange = async () => {
  if (dateRange.value && dateRange.value[0] && dateRange.value[1]) {
    const params: any = {}
    params.start = dateRange.value[0].toISOString()
    params.end = dateRange.value[1].toISOString()
    await alertStore.fetchAlerts(params)
  } else {
    await alertStore.fetchAlerts()
  }
}

const resetFilters = async () => {
  filters.severity = undefined
  filters.resolved = undefined
  filters.server_id = undefined
  dateRange.value = null
  await alertStore.fetchAlerts()
}

const goToServer = (serverId: string) => {
  router.push(`/servers/${serverId}`)
}

const handleView = (row: any) => {
  ElMessage.info('Alert detail view coming soon')
}

const handleResolve = async (row: any) => {
  try {
    await alertStore.resolveAlert(row.id)
    ElMessage.success('Alert resolved successfully')
    await alertStore.fetchAlerts()
    await alertStore.fetchStats()
  } catch (error: any) {
    console.error('Resolve alert error:', error)
    ElMessage.error(error.message || 'Failed to resolve alert')
  }
}

const handleDelete = async (row: any) => {
  try {
    await alertStore.deleteAlert(row.id)
    ElMessage.success('Alert deleted successfully')
    await alertStore.fetchAlerts()
    await alertStore.fetchStats()
  } catch (error: any) {
    console.error('Delete alert error:', error)
    ElMessage.error(error.message || 'Failed to delete alert')
  }
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return

    createLoading.value = true

    await alertStore.createAlert(createForm)

    ElMessage.success('Alert created successfully')
    showCreateDialog.value = false

    // Reset form
    createFormRef.value.resetFields()

    // Refresh alerts
    await alertStore.fetchAlerts()
    await alertStore.fetchStats()
  } catch (error: any) {
    console.error('Create alert error:', error)
    ElMessage.error(error.message || 'Failed to create alert')
  } finally {
    createLoading.value = false
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

  // Fetch alerts and stats
  await alertStore.fetchAlerts()
  await alertStore.fetchStats()
})
</script>

<style scoped lang="scss">
.alerts-container {
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
      margin: 0 0 8px 0;
    }

    .page-subtitle {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1rem;
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

    &.stat-icon-warning {
      background: rgba(255, 152, 0, 0.1);
      color: #ff9800;
    }

    &.stat-icon-critical {
      background: rgba(115, 30, 37, 0.1);
      color: #731e25;
    }

    &.stat-icon-success {
      background: rgba(20, 198, 203, 0.1);
      color: #14c6cb;
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

.filters-section {
  padding: 20px;
  margin-bottom: 24px;

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
  }
}

.alerts-table {
  padding: 20px;
}

// Responsive design
@media (max-width: 768px) {
  .alerts-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .header-left .page-title {
      font-size: 1.5rem;
    }
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .filters-section .filter-form {
    flex-direction: column;
  }
}
</style>

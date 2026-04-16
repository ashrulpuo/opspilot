<template>
  <div class="deployments-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Deployments</h1>
        <p class="page-subtitle">Manage and monitor deployments across your infrastructure</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          New Deployment
        </el-button>
        <el-button @click="switchTab">
          <el-icon><Clock /></el-icon>
          {{ currentTab === 'deployments' ? 'History' : 'Deployments' }}
        </el-button>
      </div>
    </div>

    <!-- Organization Selector -->
    <div class="org-selector" v-if="orgStore.organizations.length > 1">
      <el-select v-model="selectedOrgId" placeholder="Select organization" @change="handleOrgChange">
        <el-option v-for="org in orgStore.organizations" :key="org.id" :label="org.name" :value="org.id" />
      </el-select>
    </div>

    <!-- Stats Cards (Deployments Tab) -->
    <div class="stats-grid" v-if="currentTab === 'deployments'">
      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-primary">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Total Deployments</p>
          <p class="stat-value">{{ deploymentsStore.deployments.length }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-success">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Active</p>
          <p class="stat-value">{{ activeDeploymentsCount }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-warning">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Pending</p>
          <p class="stat-value">{{ pendingDeploymentsCount }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-critical">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Failed</p>
          <p class="stat-value">{{ failedDeploymentsCount }}</p>
        </div>
      </div>
    </div>

    <!-- Stats Cards (History Tab) -->
    <div class="stats-grid" v-else>
      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-primary">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Total Executions</p>
          <p class="stat-value">{{ executionsStore.executions.length }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-success">
          <el-icon><SuccessFilled /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Successful</p>
          <p class="stat-value">{{ successfulExecutionsCount }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-critical">
          <el-icon><CircleCloseFilled /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Failed</p>
          <p class="stat-value">{{ failedExecutionsCount }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-info">
          <el-icon><Promotion /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Rollbacks</p>
          <p class="stat-value">{{ rollbackExecutionsCount }}</p>
        </div>
      </div>
    </div>

    <!-- Deployments List -->
    <div class="deployments-list hc-card" v-if="currentTab === 'deployments'">
      <!-- Filters -->
      <div class="filters-section">
        <el-form :inline="true" :model="filters" class="filter-form">
          <el-form-item label="Deployment Type">
            <el-select v-model="filters.deployment_type" placeholder="All" clearable @change="handleFilterChange">
              <el-option label="Manual" value="manual" />
              <el-option label="Scheduled" value="scheduled" />
              <el-option label="Git" value="git" />
              <el-option label="Docker" value="docker" />
            </el-select>
          </el-form-item>

          <el-form-item label="Status">
            <el-select v-model="filters.status" placeholder="All" clearable @change="handleFilterChange">
              <el-option label="Pending" value="pending" />
              <el-option label="Running" value="running" />
              <el-option label="Completed" value="completed" />
              <el-option label="Failed" value="failed" />
              <el-option label="Rolled Back" value="rolled_back" />
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

          <el-form-item>
            <el-button @click="resetFilters">Reset</el-button>
          </el-form-item>

          <el-form-item>
            <el-button @click="handleRefresh" :loading="refreshing">
              <el-icon><Refresh /></el-icon>
              Refresh
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Table -->
      <el-table :data="deploymentsStore.deployments" v-loading="deploymentsStore.loading" style="width: 100%">
        <el-table-column prop="name" label="Name" min-width="200" />

        <el-table-column prop="deployment_type" label="Type" width="120">
          <template #default="{ row }">
            <el-tag size="small">
              {{ row.deployment_type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="server_hostname" label="Server" width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="goToServer(row.server_id)">
              {{ row.server_hostname || 'Unknown' }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ row.status.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="schedule_type" label="Schedule" width="120">
          <template #default="{ row }">
            {{ row.schedule_type || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="Created" width="180">
          <template #default="{ row }">
            {{ formatTimestamp(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">
              <el-icon><View /></el-icon>
              View
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              Edit
            </el-button>
            <el-button link type="primary" size="small" @click="handleExecute(row)">
              <el-icon><Promotion /></el-icon>
              Execute
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!deploymentsStore.loading && deploymentsStore.deployments.length === 0"
        description="No deployments found. Create your first deployment."
      />
    </div>

    <!-- Deployment History -->
    <div class="history-list hc-card" v-else>
      <!-- Filters -->
      <div class="filters-section">
        <el-form :inline="true" :model="historyFilters" class="filter-form">
          <el-form-item label="Status">
            <el-select v-model="historyFilters.status" placeholder="All" clearable @change="handleHistoryFilterChange">
              <el-option label="Pending" value="pending" />
              <el-option label="Queued" value="queued" />
              <el-option label="Running" value="running" />
              <el-option label="Completed" value="completed" />
              <el-option label="Failed" value="failed" />
            </el-select>
          </el-form-item>

          <el-form-item label="Server">
            <el-select
              v-model="historyFilters.server_id"
              placeholder="All"
              clearable
              filterable
              @change="handleHistoryFilterChange"
            >
              <el-option
                v-for="server in serverStore.servers"
                :key="server.id"
                :label="server.hostname"
                :value="server.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button @click="resetHistoryFilters">Reset</el-button>
          </el-form-item>

          <el-form-item>
            <el-button @click="handleHistoryRefresh" :loading="historyRefreshing">
              <el-icon><Refresh /></el-icon>
              Refresh
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Table -->
      <el-table :data="executionsStore.executions" v-loading="executionsStore.loading" style="width: 100%">
        <el-table-column prop="deployment_name" label="Deployment" min-width="200" />

        <el-table-column prop="server_hostname" label="Server" width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="goToServer(row.server_id)">
              {{ row.server_hostname || 'Unknown' }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ row.status.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="dry_run" label="Dry Run" width="100">
          <template #default="{ row }">
            <el-tag :type="row.dry_run ? 'info' : ''" size="small">
              {{ row.dry_run ? 'Yes' : 'No' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="duration_seconds" label="Duration" width="120">
          <template #default="{ row }">
            {{ row.duration_seconds ? `${row.duration_seconds}s` : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="started_at" label="Started" width="180">
          <template #default="{ row }">
            {{ formatTimestamp(row.started_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleViewExecution(row)">
              <el-icon><View /></el-icon>
              View
            </el-button>
            <el-button v-if="row.status === 'completed'" link type="warning" size="small" @click="handleRollback(row)">
              <el-icon><RefreshLeft /></el-icon>
              Rollback
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!executionsStore.loading && executionsStore.executions.length === 0"
        description="No deployment history found."
      />
    </div>

    <!-- Create/Edit Deployment Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingDeployment ? 'Edit Deployment' : 'New Deployment'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form ref="deployFormRef" :model="deployForm" :rules="deployFormRules" label-width="140px">
        <el-form-item label="Deployment Name" prop="name">
          <el-input v-model="deployForm.name" placeholder="e.g., Frontend Update, Database Migration" />
        </el-form-item>

        <el-form-item label="Description">
          <el-input
            v-model="deployForm.description"
            type="textarea"
            :rows="3"
            placeholder="Description of this deployment"
          />
        </el-form-item>

        <el-form-item label="Server" prop="server_id">
          <el-select v-model="deployForm.server_id" placeholder="Select server" style="width: 100%">
            <el-option
              v-for="server in serverStore.servers"
              :key="server.id"
              :label="server.hostname"
              :value="server.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Deployment Type" prop="deployment_type">
          <el-select v-model="deployForm.deployment_type" placeholder="Select type" style="width: 100%">
            <el-option label="Manual (Custom Script)" value="manual" />
            <el-option label="Scheduled (Cron)" value="scheduled" />
            <el-option label="Git (Clone/Update)" value="git" />
            <el-option label="Docker (Build/Deploy)" value="docker" />
          </el-select>
        </el-form-item>

        <el-form-item label="Schedule Type">
          <el-radio-group v-model="deployForm.schedule_type">
            <el-radio value="immediate">Immediate</el-radio>
            <el-radio value="scheduled">Scheduled</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="deployForm.schedule_type === 'scheduled'" label="Cron Expression" prop="schedule_value">
          <el-input v-model="deployForm.schedule_value" placeholder="e.g., 0 2 * * * (2 AM daily)" />
        </el-form-item>

        <el-divider>Configuration</el-divider>

        <el-form-item label="Script / Command">
          <el-input
            v-model="deployForm.config.script"
            type="textarea"
            :rows="6"
            placeholder="Script to execute (for manual deployments)"
          />
        </el-form-item>

        <el-form-item label="Git Repository URL">
          <el-input v-model="deployForm.config.git_repo" placeholder="https://github.com/user/repo.git" />
        </el-form-item>

        <el-form-item label="Docker Image">
          <el-input v-model="deployForm.config.docker_image" placeholder="nginx:latest" />
        </el-form-item>

        <el-form-item label="Environment Variables">
          <el-input
            v-model="deployForm.config.env_vars"
            type="textarea"
            :rows="3"
            placeholder="KEY=value (one per line)"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          {{ editingDeployment ? 'Update' : 'Create' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Execute Deployment Dialog -->
    <el-dialog v-model="showExecuteDialog" title="Execute Deployment" width="600px" :close-on-click-modal="false">
      <el-form ref="executeFormRef" :model="executeForm" label-width="140px">
        <el-form-item label="Deployment Name">
          <el-input :model-value="executingDeployment?.name ?? ''" disabled />
        </el-form-item>

        <el-form-item label="Server">
          <el-input :model-value="executingDeployment?.server_hostname ?? ''" disabled />
        </el-form-item>

        <el-form-item label="Dry Run">
          <el-switch v-model="executeForm.dry_run" />
          <div style="color: #656a76; font-size: 12px; margin-top: 4px">
            Dry run will simulate the deployment without making changes.
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showExecuteDialog = false">Cancel</el-button>
        <el-button type="primary" @click="handleExecuteConfirm" :loading="executing"> Execute </el-button>
      </template>
    </el-dialog>

    <!-- Rollback Dialog -->
    <el-dialog v-model="showRollbackDialog" title="Rollback Deployment" width="600px" :close-on-click-modal="false">
      <el-form :model="rollbackForm" label-width="140px">
        <el-form-item label="Execution ID">
          <el-input :model-value="rollingBackExecution?.id ?? ''" disabled />
        </el-form-item>

        <el-form-item label="Deployment Name">
          <el-input :model-value="rollingBackExecution?.deployment_name ?? ''" disabled />
        </el-form-item>

        <el-form-item label="Reason for Rollback">
          <el-input v-model="rollbackForm.reason" type="textarea" :rows="3" placeholder="Why are you rolling back?" />
        </el-form-item>

        <el-alert title="Warning" type="warning" :closable="false" style="margin-bottom: 16px">
          Rolling back will revert the deployment to the previous version. This action cannot be undone.
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="showRollbackDialog = false">Cancel</el-button>
        <el-button type="danger" @click="handleRollbackConfirm" :loading="rollingBack"> Rollback </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Document,
  CircleCheck,
  Loading,
  CircleClose,
  Clock,
  SuccessFilled,
  CircleCloseFilled,
  Promotion,
  Refresh,
  View,
  Edit,
  Delete,
  RefreshLeft,
} from '@element-plus/icons-vue'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'
import { useOpsPilotServerStore } from '@/stores/modules/opspilot'
import { DeploymentsAPI } from '@/api/opspilot/deployments'

const router = useRouter()
const orgStore = useOpsPilotOrganizationStore()
const serverStore = useOpsPilotServerStore()

// Mock deployment store (TODO: create actual store)
const deploymentsStore = reactive({
  deployments: [] as any[],
  loading: false,
})

// Mock executions store (TODO: create actual store)
const executionsStore = reactive({
  executions: [] as any[],
  loading: false,
})

const currentTab = ref<'deployments' | 'history'>('deployments')
const showCreateDialog = ref(false)
const showExecuteDialog = ref(false)
const showRollbackDialog = ref(false)
const refreshing = ref(false)
const historyRefreshing = ref(false)
const creating = ref(false)
const executing = ref(false)
const rollingBack = ref(false)
const deployFormRef = ref<FormInstance>()
const executeFormRef = ref<FormInstance>()
const selectedOrgId = ref<string>()
const editingDeployment = ref<any>(null)
const executingDeployment = ref<any>(null)
const rollingBackExecution = ref<any>(null)

const deployForm = reactive({
  name: '',
  description: '',
  server_id: '',
  deployment_type: 'manual',
  schedule_type: 'immediate',
  schedule_value: '',
  config: {
    script: '',
    git_repo: '',
    docker_image: '',
    env_vars: '',
  },
})

const executeForm = reactive({
  dry_run: false,
})

const rollbackForm = reactive({
  reason: '',
})

const deployFormRules: FormRules = {
  name: [{ required: true, message: 'Deployment name is required', trigger: 'blur' }],
  server_id: [{ required: true, message: 'Server is required', trigger: 'change' }],
  deployment_type: [{ required: true, message: 'Deployment type is required', trigger: 'change' }],
  schedule_value: [
    { required: true, message: 'Cron expression is required for scheduled deployments', trigger: 'blur' },
  ],
}

const filters = reactive({
  deployment_type: undefined as string | undefined,
  status: undefined as string | undefined,
  server_id: undefined as string | undefined,
})

const historyFilters = reactive({
  status: undefined as string | undefined,
  server_id: undefined as string | undefined,
})

const activeDeploymentsCount = computed(
  () => deploymentsStore.deployments.filter((d: any) => d.status === 'completed' || d.status === 'running').length
)

const pendingDeploymentsCount = computed(
  () => deploymentsStore.deployments.filter((d: any) => d.status === 'pending').length
)

const failedDeploymentsCount = computed(
  () => deploymentsStore.deployments.filter((d: any) => d.status === 'failed').length
)

const successfulExecutionsCount = computed(
  () => executionsStore.executions.filter((e: any) => e.status === 'completed').length
)

const failedExecutionsCount = computed(
  () => executionsStore.executions.filter((e: any) => e.status === 'failed').length
)

const rollbackExecutionsCount = computed(
  () =>
    executionsStore.executions.filter(
      (e: any) => e.deployment_name?.includes('Rollback') || e.output?.includes('rollback')
    ).length
)

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'running':
    case 'queued':
      return 'warning'
    case 'failed':
      return 'danger'
    case 'pending':
    case 'rolled_back':
      return 'info'
    default:
      return ''
  }
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const switchTab = () => {
  currentTab.value = currentTab.value === 'deployments' ? 'history' : 'deployments'
}

const handleOrgChange = async (orgId: string) => {
  await serverStore.fetchServers(orgId)
  await fetchDeployments(orgId)
  await fetchExecutions(orgId)
}

const handleFilterChange = async () => {
  await fetchDeployments(selectedOrgId.value)
}

const handleHistoryFilterChange = async () => {
  await fetchExecutions(selectedOrgId.value)
}

const resetFilters = async () => {
  filters.deployment_type = undefined
  filters.status = undefined
  filters.server_id = undefined
  await fetchDeployments(selectedOrgId.value)
}

const resetHistoryFilters = async () => {
  historyFilters.status = undefined
  historyFilters.server_id = undefined
  await fetchExecutions(selectedOrgId.value)
}

const handleRefresh = async () => {
  refreshing.value = true
  await fetchDeployments(selectedOrgId.value)
  refreshing.value = false
}

const handleHistoryRefresh = async () => {
  historyRefreshing.value = true
  await fetchExecutions(selectedOrgId.value)
  historyRefreshing.value = false
}

const handleView = (row: any) => {
  ElMessage.info('Deployment detail view coming soon')
}

const handleEdit = (row: any) => {
  editingDeployment.value = row
  deployForm.name = row.name
  deployForm.description = row.description || ''
  deployForm.server_id = row.server_id
  deployForm.deployment_type = row.deployment_type
  deployForm.schedule_type = row.schedule_type || 'immediate'
  deployForm.schedule_value = row.schedule_value || ''
  showCreateDialog.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`Are you sure you want to delete deployment "${row.name}"?`, 'Delete Deployment', {
      type: 'warning',
    })

    await DeploymentsAPI.delete(row.id)
    ElMessage.success('Deployment deleted successfully')
    await fetchDeployments(selectedOrgId.value)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Delete deployment error:', error)
      ElMessage.error(error.message || 'Failed to delete deployment')
    }
  }
}

const handleExecute = (row: any) => {
  executingDeployment.value = row
  executeForm.dry_run = false
  showExecuteDialog.value = true
}

const handleExecuteConfirm = async () => {
  try {
    executing.value = true

    const result = await DeploymentsAPI.execute(executingDeployment.value.id, {
      dry_run: executeForm.dry_run,
    })

    ElMessage.success(`Deployment ${executeForm.dry_run ? '(dry run) ' : ''}queued for execution`)
    showExecuteDialog.value = false

    await fetchExecutions(selectedOrgId.value)
  } catch (error: any) {
    console.error('Execute deployment error:', error)
    ElMessage.error(error.message || 'Failed to execute deployment')
  } finally {
    executing.value = false
  }
}

const handleRollback = (row: any) => {
  rollingBackExecution.value = row
  rollbackForm.reason = ''
  showRollbackDialog.value = true
}

const handleRollbackConfirm = async () => {
  try {
    rollingBack.value = true

    await DeploymentsAPI.rollback(rollingBackExecution.value.deployment_id, {
      reason: rollbackForm.reason,
    })

    ElMessage.success('Rollback queued for execution')
    showRollbackDialog.value = false

    await fetchExecutions(selectedOrgId.value)
  } catch (error: any) {
    console.error('Rollback error:', error)
    ElMessage.error(error.message || 'Failed to rollback deployment')
  } finally {
    rollingBack.value = false
  }
}

const handleCreate = async () => {
  if (!deployFormRef.value) return

  await deployFormRef.value.validate(async valid => {
    if (!valid) return

    try {
      creating.value = true

      const orgId = selectedOrgId.value || orgStore.currentOrganization?.id
      if (!orgId) {
        ElMessage.error('No organization selected')
        return
      }

      // Parse environment variables
      const envVars: Record<string, string> = {}
      if (deployForm.config.env_vars) {
        deployForm.config.env_vars.split('\n').forEach(line => {
          const [key, value] = line.split('=')
          if (key && value) {
            envVars[key.trim()] = value.trim()
          }
        })
      }

      const data = {
        ...deployForm,
        config: {
          ...deployForm.config,
          env_vars: envVars,
        },
      }

      if (editingDeployment.value) {
        // Update
        await DeploymentsAPI.update(editingDeployment.value.id, data)
        ElMessage.success('Deployment updated successfully')
      } else {
        // Create
        await DeploymentsAPI.create(orgId, data)
        ElMessage.success('Deployment created successfully')
      }

      showCreateDialog.value = false
      editingDeployment.value = null
      resetDeployForm()

      await fetchDeployments(orgId)
    } catch (error: any) {
      console.error('Create/Update deployment error:', error)
      ElMessage.error(error.message || 'Failed to create/update deployment')
    } finally {
      creating.value = false
    }
  })
}

const resetDeployForm = () => {
  deployForm.name = ''
  deployForm.description = ''
  deployForm.server_id = ''
  deployForm.deployment_type = 'manual'
  deployForm.schedule_type = 'immediate'
  deployForm.schedule_value = ''
  deployForm.config.script = ''
  deployForm.config.git_repo = ''
  deployForm.config.docker_image = ''
  deployForm.config.env_vars = ''
}

const handleViewExecution = (row: any) => {
  ElMessage.info('Execution detail view coming soon')
}

const goToServer = (serverId: string) => {
  router.push(`/servers/${serverId}`)
}

const fetchDeployments = async (organizationId?: string) => {
  try {
    const orgId = organizationId || selectedOrgId.value || orgStore.currentOrganization?.id
    if (!orgId) {
      ElMessage.error('No organization selected')
      return
    }

    deploymentsStore.loading = true

    const params: any = {}
    if (filters.deployment_type) params.deployment_type = filters.deployment_type
    if (filters.status) params.status_filter = filters.status
    if (filters.server_id) params.server_id = filters.server_id

    // TODO: Create deployments store
    const response = await DeploymentsAPI.list(params)
    deploymentsStore.deployments = response.items
  } catch (error: any) {
    console.error('Fetch deployments error:', error)
    ElMessage.error(error.message || 'Failed to fetch deployments')
  } finally {
    deploymentsStore.loading = false
  }
}

const fetchExecutions = async (organizationId?: string) => {
  try {
    const orgId = organizationId || selectedOrgId.value || orgStore.currentOrganization?.id
    if (!orgId) {
      ElMessage.error('No organization selected')
      return
    }

    executionsStore.loading = true

    const params: any = {}
    if (historyFilters.status) params.status_filter = historyFilters.status
    if (historyFilters.server_id) params.server_id = historyFilters.server_id

    const response = await DeploymentsAPI.listHistory(params)
    executionsStore.executions = response.items
  } catch (error: any) {
    console.error('Fetch executions error:', error)
    ElMessage.error(error.message || 'Failed to fetch deployment history')
  } finally {
    executionsStore.loading = false
  }
}

onMounted(async () => {
  if (orgStore.organizations.length === 0) {
    await orgStore.fetchOrganizations()
  }

  selectedOrgId.value = orgStore.currentOrganization?.id

  await serverStore.fetchServers(selectedOrgId.value)

  await fetchDeployments(selectedOrgId.value)
  await fetchExecutions(selectedOrgId.value)
})
</script>

<style scoped lang="scss">
.deployments-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;

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

  .header-actions {
    display: flex;
    gap: 12px;
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
      background: rgba(4, 133, 64, 0.1);
      color: #048540;
    }

    &.stat-icon-warning {
      background: rgba(255, 152, 0, 0.1);
      color: #ff9800;
    }

    &.stat-icon-critical {
      background: rgba(115, 30, 37, 0.1);
      color: #731e25;
    }

    &.stat-icon-info {
      background: rgba(33, 150, 243, 0.1);
      color: #2196f3;
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

.deployments-list,
.history-list {
  padding: 20px;
}

.filters-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #dfe1e6;

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
  }
}

html.dark .filters-section {
  border-bottom-color: #5c5f66;
}

// Responsive design
@media (max-width: 768px) {
  .deployments-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;

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

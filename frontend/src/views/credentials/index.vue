<template>
  <div class="credentials-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Credentials</h1>
        <p class="page-subtitle">Securely manage SSH keys, passwords, and tokens</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Key /></el-icon>
        Add Credential
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
          <el-icon><Key /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Total Credentials</p>
          <p class="stat-value">{{ credentials.length }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-info">
          <el-icon><Lock /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">SSH Keys</p>
          <p class="stat-value">{{ sshKeyCount }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-warning">
          <el-icon><Files /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Passwords</p>
          <p class="stat-value">{{ passwordCount }}</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-success">
          <el-icon><Coordinate /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">API Keys</p>
          <p class="stat-value">{{ apiKeyCount }}</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section hc-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="Type">
          <el-select v-model="filters.credential_type" placeholder="All" clearable @change="handleFilterChange">
            <el-option label="SSH Key" value="ssh_key" />
            <el-option label="Password" value="password" />
            <el-option label="API Key" value="api_key" />
            <el-option label="Token" value="token" />
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
      </el-form>
    </div>

    <!-- Credentials Table -->
    <div class="credentials-table hc-card">
      <el-table :data="credentials" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="Name" min-width="200">
          <template #default="{ row }">
            <div class="credential-name-cell">
              <div class="name-text">{{ row.name }}</div>
              <div class="description-text" v-if="row.description">{{ row.description }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="Type" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)" size="small">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="server_hostname" label="Server" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToServer(row.server_id)">
              {{ row.server_hostname || 'Unknown' }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="Last Updated" width="160">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Actions" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleRotate(row)">
              <el-icon><Refresh /></el-icon>
              Rotate
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              Edit
            </el-button>
            <el-popconfirm title="Are you sure you want to delete this credential?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && credentials.length === 0"
        description="No credentials found. Add your first credential to get started."
      />
    </div>

    <!-- Create/Edit Credential Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEditing ? 'Edit Credential' : 'Add Credential'"
      width="600px"
      :close-on-click-modal="false"
    >
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

        <el-form-item label="Name" prop="name">
          <el-input v-model="createForm.name" placeholder="Credential name" />
        </el-form-item>

        <el-form-item label="Type" prop="type">
          <el-select v-model="createForm.type" placeholder="Select type" style="width: 100%">
            <el-option label="SSH Key" value="ssh_key" />
            <el-option label="Password" value="password" />
            <el-option label="API Key" value="api_key" />
            <el-option label="Token" value="token" />
          </el-select>
        </el-form-item>

        <el-form-item label="Value" prop="value">
          <el-input v-model="createForm.value" :type="showValue ? 'text' : 'password'" placeholder="Credential value">
            <template #suffix>
              <el-icon @click="showValue = !showValue">
                <View v-if="!showValue" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="Description">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="Optional description" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="closeCreateDialog">Cancel</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createLoading">
          {{ isEditing ? 'Save' : 'Add' }} Credential
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Key, Lock, Files, Coordinate, Refresh, Edit, Delete, View, Hide } from '@element-plus/icons-vue'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'
import { useOpsPilotServerStore } from '@/stores/modules/opspilot'
import { CredentialsAPI } from '@/api/opspilot/credentials'

const router = useRouter()
const orgStore = useOpsPilotOrganizationStore()
const serverStore = useOpsPilotServerStore()

const showCreateDialog = ref(false)
const createLoading = ref(false)
const isEditing = ref(false)
const showValue = ref(false)
const createFormRef = ref<FormInstance>()
const selectedOrgId = ref<string>()
const loading = ref(false)
const credentials = ref<any[]>([])

const createForm = reactive({
  id: '',
  server_id: '',
  name: '',
  type: 'password' as 'ssh_key' | 'password' | 'api_key' | 'token',
  value: '',
  description: '',
})

const filters = reactive({
  credential_type: undefined as string | undefined,
  server_id: undefined as string | undefined,
})

const createRules: FormRules = {
  server_id: [{ required: true, message: 'Please select a server', trigger: 'change' }],
  name: [{ required: true, message: 'Please enter a name', trigger: 'blur' }],
  type: [{ required: true, message: 'Please select a type', trigger: 'change' }],
  value: [{ required: true, message: 'Please enter a value', trigger: 'blur' }],
}

const sshKeyCount = computed(() => credentials.value.filter(c => c.type === 'ssh_key').length)
const passwordCount = computed(() => credentials.value.filter(c => c.type === 'password').length)
const apiKeyCount = computed(() => credentials.value.filter(c => c.type === 'api_key').length)

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    ssh_key: 'SSH Key',
    password: 'Password',
    api_key: 'API Key',
    token: 'Token',
    unknown: 'Unknown',
  }
  return labels[type] || 'Unknown'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, any> = {
    ssh_key: 'primary',
    password: 'warning',
    api_key: 'info',
    token: 'success',
    unknown: 'info',
  }
  return colors[type] || 'info'
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
  await fetchCredentials(orgId)
}

const handleFilterChange = async () => {
  await fetchCredentials(selectedOrgId.value)
}

const resetFilters = async () => {
  filters.credential_type = undefined
  filters.server_id = undefined
  await fetchCredentials(selectedOrgId.value)
}

const goToServer = (serverId: string) => {
  router.push(`/servers/${serverId}`)
}

const handleEdit = (row: any) => {
  isEditing.value = true
  createForm.id = row.id
  createForm.server_id = row.server_id
  createForm.name = row.name
  createForm.type = row.type
  createForm.value = ''
  createForm.description = row.description || ''
  showCreateDialog.value = true
}

const handleRotate = async (row: any) => {
  try {
    await CredentialsAPI.rotate(row.id)
    ElMessage.success('Credential rotated successfully')
    await fetchCredentials(selectedOrgId.value)
  } catch (error: any) {
    console.error('Rotate credential error:', error)
    ElMessage.error(error.message || 'Failed to rotate credential')
  }
}

const handleDelete = async (row: any) => {
  try {
    await CredentialsAPI.delete(row.id)
    ElMessage.success('Credential deleted successfully')
    await fetchCredentials(selectedOrgId.value)
  } catch (error: any) {
    console.error('Delete credential error:', error)
    ElMessage.error(error.message || 'Failed to delete credential')
  }
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return

    const orgId = selectedOrgId.value || orgStore.currentOrganization?.id
    if (!orgId) {
      ElMessage.error('No organization selected')
      return
    }

    createLoading.value = true

    if (isEditing.value) {
      await CredentialsAPI.update(createForm.id, {
        name: createForm.name,
        description: createForm.description,
        data: { value: createForm.value },
      })
      ElMessage.success('Credential updated successfully')
    } else {
      await CredentialsAPI.create(orgId, {
        server_id: createForm.server_id,
        name: createForm.name,
        type: createForm.type,
        data: { value: createForm.value },
        description: createForm.description,
      })
      ElMessage.success('Credential added successfully')
    }

    closeCreateDialog()
    await fetchCredentials(orgId)
  } catch (error: any) {
    console.error('Save credential error:', error)
    ElMessage.error(error.message || 'Failed to save credential')
  } finally {
    createLoading.value = false
  }
}

const closeCreateDialog = () => {
  showCreateDialog.value = false
  isEditing.value = false
  if (createFormRef.value) {
    createFormRef.value.resetFields()
  }
  createForm.value = ''
}

const fetchCredentials = async (organizationId?: string) => {
  try {
    loading.value = true
    const params: any = {}
    if (filters.credential_type) params.credential_type = filters.credential_type
    if (filters.server_id) params.server_id = filters.server_id

    const response = await CredentialsAPI.list(params)
    credentials.value = response.items
  } catch (error: any) {
    console.error('Fetch credentials error:', error)
    ElMessage.error(error.message || 'Failed to fetch credentials')
  } finally {
    loading.value = false
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

  // Fetch credentials
  await fetchCredentials(selectedOrgId.value)
})
</script>

<style scoped lang="scss">
.credentials-container {
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

    &.stat-icon-info {
      background: rgba(33, 150, 243, 0.1);
      color: #2196f3;
    }

    &.stat-icon-warning {
      background: rgba(255, 152, 0, 0.1);
      color: #ff9800;
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

.credentials-table {
  padding: 20px;

  .credential-name-cell {
    .name-text {
      font-weight: 500;
      color: #000000;
    }

    .description-text {
      font-size: 0.8125rem;
      color: #656a76;
      margin-top: 4px;
    }
  }
}

html.dark .credentials-table .credential-name-cell .name-text {
  color: #ffffff;
}

// Responsive design
@media (max-width: 768px) {
  .credentials-container {
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

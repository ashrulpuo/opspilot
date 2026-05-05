<template>
  <div class="registry-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Infrastructure Registry</h1>
        <p class="page-subtitle">Domains, SSL certificates, databases, and credentials — encrypted at rest</p>
      </div>
      <el-button v-if="activeTab !== 'audit'" type="primary" :icon="Plus" @click="openAdd">Add Asset</el-button>
    </div>

    <el-tabs v-model="activeTab" class="registry-tabs">
      <el-tab-pane label="Domains" name="domains">
        <DomainList :items="domains" :loading="loading" @edit="openEdit" @delete="handleDelete('domain', $event)" />
      </el-tab-pane>
      <el-tab-pane label="SSL Certs" name="ssl">
        <SslCertList :items="sslCerts" :loading="loading" @edit="openEdit" @delete="handleDelete('ssl', $event)" />
      </el-tab-pane>
      <el-tab-pane label="Databases" name="databases">
        <DatabaseList :items="databases" :loading="loading" @edit="openEdit" @delete="handleDelete('db', $event)" />
      </el-tab-pane>
      <el-tab-pane label="Credentials" name="credentials">
        <CredentialList :items="credentials" :loading="loading" @edit="openEdit" @delete="handleDelete('cred', $event)" />
      </el-tab-pane>
      <el-tab-pane label="Audit Log" name="audit">
        <AuditLogTable :items="auditLog" :loading="loading" />
      </el-tab-pane>
    </el-tabs>

    <RegistryForm
      v-model="formVisible"
      :type="formTab"
      :item="editingItem"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  RegistryAPI,
  type Domain, type SslCert, type DbService, type Credential, type AuditLog,
} from '@/api/opspilot/registry'
import DomainList from './components/DomainList.vue'
import SslCertList from './components/SslCertList.vue'
import DatabaseList from './components/DatabaseList.vue'
import CredentialList from './components/CredentialList.vue'
import AuditLogTable from './components/AuditLogTable.vue'
import RegistryForm from './components/RegistryForm.vue'

const activeTab = ref('domains')
const formTab = computed(() => activeTab.value === 'audit' ? 'domains' : activeTab.value)

const loading = ref(false)
const formVisible = ref(false)
const editingItem = ref<Record<string, unknown> | null>(null)

const domains = ref<Domain[]>([])
const sslCerts = ref<SslCert[]>([])
const databases = ref<DbService[]>([])
const credentials = ref<Credential[]>([])
const auditLog = ref<AuditLog[]>([])

onMounted(load)
watch(activeTab, load)

async function load() {
  loading.value = true
  try {
    if (activeTab.value === 'domains') domains.value = await RegistryAPI.listDomains()
    else if (activeTab.value === 'ssl') sslCerts.value = await RegistryAPI.listSslCerts()
    else if (activeTab.value === 'databases') databases.value = await RegistryAPI.listDatabases()
    else if (activeTab.value === 'credentials') credentials.value = await RegistryAPI.listCredentials()
    else if (activeTab.value === 'audit') auditLog.value = await RegistryAPI.getAuditLog()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingItem.value = null
  formVisible.value = true
}

function openEdit(item: Record<string, unknown>) {
  editingItem.value = item
  formVisible.value = true
}

async function handleDelete(type: string, id: string) {
  await ElMessageBox.confirm('Delete this asset? This cannot be undone.', 'Delete', {
    type: 'warning', confirmButtonText: 'Delete', confirmButtonClass: 'el-button--danger',
  }).catch(() => { throw new Error('cancelled') })
  if (type === 'domain') await RegistryAPI.deleteDomain(id)
  else if (type === 'ssl') await RegistryAPI.deleteSslCert(id)
  else if (type === 'db') await RegistryAPI.deleteDatabase(id)
  else if (type === 'cred') await RegistryAPI.deleteCredential(id)
  ElMessage.success('Deleted')
  await load()
}

async function handleSubmit(data: Record<string, unknown>) {
  const tab = formTab.value
  const id = editingItem.value?.id as string | undefined
  if (tab === 'domains') {
    if (id) await RegistryAPI.updateDomain(id, data)
    else await RegistryAPI.createDomain(data)
  } else if (tab === 'ssl') {
    if (id) await RegistryAPI.updateSslCert(id, data)
    else await RegistryAPI.createSslCert(data)
  } else if (tab === 'databases') {
    if (id) await RegistryAPI.updateDatabase(id, data)
    else await RegistryAPI.createDatabase(data)
  } else if (tab === 'credentials') {
    if (id) await RegistryAPI.updateCredential(id, data)
    else await RegistryAPI.createCredential(data)
  }
  ElMessage.success(id ? 'Updated' : 'Created')
  await load()
}
</script>

<style scoped>
.registry-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 4px;
}
.page-subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0;
}
.registry-tabs {
  background: var(--el-bg-color);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  padding: 0 16px 16px;
}
</style>

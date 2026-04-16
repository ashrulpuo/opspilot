<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-header__text">
        <h1 class="page-title">Organizations</h1>
        <p class="page-subtitle">Manage workspaces, edit settings, and see servers in each org.</p>
      </div>
      <el-button type="primary" @click.stop="openCreateDialog">Create organization</el-button>
    </div>

    <div class="org-list-region" v-loading="orgStore.loading">
      <div v-if="!orgStore.loading && orgStore.organizations.length === 0" class="hc-card org-empty-wrap">
        <el-empty description="No organizations yet. Use Create Organization to add one." />
      </div>

      <div v-else-if="orgStore.organizations.length > 0" class="org-cards">
        <article
          v-for="org in orgStore.organizations"
          :key="org.id"
          class="org-card hc-card"
          :class="{ 'org-card--current': org.id === orgStore.currentOrganization?.id }"
        >
          <div class="org-card__top">
            <div class="org-card__identity">
              <div class="org-card__icon" aria-hidden="true">
                <el-icon :size="24"><OfficeBuilding /></el-icon>
              </div>
              <div class="org-card__meta">
                <h2 class="org-card__name">{{ org.name }}</h2>
                <p class="org-card__slug">{{ org.slug }}</p>
                <div class="org-card__chips">
                  <el-tag v-if="org.id === orgStore.currentOrganization?.id" size="small" type="success">
                    Current workspace
                  </el-tag>
                  <span class="org-card__date">{{ formatDate(org.created_at) }}</span>
                </div>
              </div>
            </div>
            <div class="org-card__actions">
              <el-tooltip content="Open organization" placement="top">
                <el-button class="org-card__action-btn" aria-label="View organization" @click="goOrganization(org.id)">
                  <el-icon :size="18"><View /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="Edit name and slug" placement="top">
                <el-button class="org-card__action-btn" aria-label="Edit organization" @click="openEditDialog(org)">
                  <el-icon :size="18"><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              <el-popconfirm
                width="280"
                confirm-button-type="danger"
                title="Delete this organization? Servers and related data in this org will be removed."
                @confirm="confirmDeleteOrg(org)"
              >
                <template #reference>
                  <span class="org-card__pop-wrap">
                    <el-tooltip content="Delete organization" placement="top">
                      <el-button class="org-card__action-btn org-card__action-btn--danger" aria-label="Delete organization">
                        <el-icon :size="18"><Delete /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </span>
                </template>
              </el-popconfirm>
            </div>
          </div>

          <section class="org-card__servers" aria-label="Servers in this organization">
            <div class="org-card__servers-head">
              <span class="org-card__servers-title">
                <el-icon><Monitor /></el-icon>
                Servers
              </span>
              <el-tag v-if="!serversLoading[org.id]" size="small" type="info" effect="plain">
                {{ (serversByOrg[org.id] ?? []).length }}
              </el-tag>
            </div>
            <div v-if="serversLoading[org.id]" class="servers-loading">
              <el-skeleton :rows="2" animated />
            </div>
            <el-empty
              v-else-if="(serversByOrg[org.id] ?? []).length === 0"
              class="servers-empty"
              description="No servers in this organization"
              :image-size="56"
            />
            <div v-else class="servers-table-wrap">
              <el-table :data="serversByOrg[org.id]" size="small" stripe class="servers-mini-table">
                <el-table-column prop="hostname" label="Hostname" min-width="120" show-overflow-tooltip />
                <el-table-column prop="ip_address" label="IP" width="120" show-overflow-tooltip />
                <el-table-column label="Status" width="100">
                  <template #default="{ row }">
                    <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="" width="72" align="right">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="goServer(row.id)">Open</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </section>
        </article>
      </div>
    </div>

    <el-dialog
      v-model="showCreateDialog"
      title="Create organization"
      width="480px"
      append-to-body
      destroy-on-close
      :close-on-click-modal="false"
      @closed="resetCreateForm"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px" @submit.prevent>
        <el-form-item label="Name" prop="name">
          <el-input v-model="createForm.name" placeholder="My team" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="Slug" prop="slug">
          <el-input v-model="createForm.slug" placeholder="my-team" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="submitCreate">Create</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showEditDialog"
      title="Edit organization"
      width="480px"
      append-to-body
      destroy-on-close
      :close-on-click-modal="false"
      @closed="resetEditForm"
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px" @submit.prevent>
        <el-form-item label="Name" prop="name">
          <el-input v-model="editForm.name" placeholder="Organization name" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="Slug" prop="slug">
          <el-input v-model="editForm.slug" placeholder="url-slug" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="submitEdit">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { View, Edit, Delete, OfficeBuilding, Monitor } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { Organization, Server } from '@/api/opspilot/types'
import { ServersAPI } from '@/api/opspilot/servers'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'

const router = useRouter()
const orgStore = useOpsPilotOrganizationStore()

const showCreateDialog = ref(false)
const createSubmitting = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({ name: '', slug: '' })

const showEditDialog = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref<FormInstance>()
const editingOrgId = ref<string | null>(null)
const editForm = reactive({ name: '', slug: '' })

const serversByOrg = reactive<Record<string, Server[]>>({})
const serversLoading = reactive<Record<string, boolean>>({})

const slugPatternRule = {
  pattern: /^[a-z0-9-]+$/,
  message: 'Slug can only contain lowercase letters, numbers, and hyphens',
  trigger: 'blur' as const,
}

const createRules: FormRules = {
  name: [
    { required: true, message: 'Please enter organization name', trigger: 'blur' },
    { min: 2, message: 'Name must be at least 2 characters', trigger: 'blur' },
  ],
  slug: [
    { required: true, message: 'Please enter a slug', trigger: 'blur' },
    slugPatternRule,
  ],
}

const editRules: FormRules = {
  name: [
    { required: true, message: 'Please enter organization name', trigger: 'blur' },
    { min: 2, message: 'Name must be at least 2 characters', trigger: 'blur' },
  ],
  slug: [
    { required: true, message: 'Please enter a slug', trigger: 'blur' },
    slugPatternRule,
  ],
}

function openCreateDialog() {
  showCreateDialog.value = true
}

function resetCreateForm() {
  createForm.name = ''
  createForm.slug = ''
  createFormRef.value?.resetFields()
}

function openEditDialog(org: Organization) {
  editingOrgId.value = org.id
  editForm.name = org.name
  editForm.slug = org.slug
  showEditDialog.value = true
}

function resetEditForm() {
  editingOrgId.value = null
  editForm.name = ''
  editForm.slug = ''
  editFormRef.value?.resetFields()
}

function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function statusTagType(status: string): 'success' | 'info' | 'warning' | 'danger' {
  switch (status) {
    case 'online':
      return 'success'
    case 'error':
      return 'danger'
    case 'connecting':
      return 'warning'
    default:
      return 'info'
  }
}

function goOrganization(id: string) {
  void router.push(`/organizations/${id}`)
}

function goServer(id: string) {
  void router.push(`/servers/${id}`)
}

async function loadServersForOrg(orgId: string) {
  serversLoading[orgId] = true
  try {
    const { servers } = await ServersAPI.list(orgId)
    serversByOrg[orgId] = servers
  } catch {
    serversByOrg[orgId] = []
    ElMessage.warning('Could not load servers for one organization')
  } finally {
    serversLoading[orgId] = false
  }
}

async function refreshServersForAllOrgs() {
  const ids = orgStore.organizations.map(o => o.id)
  await Promise.all(ids.map(id => loadServersForOrg(id)))
}

async function confirmDeleteOrg(org: Organization) {
  try {
    await orgStore.deleteOrganization(org.id)
    delete serversByOrg[org.id]
    delete serversLoading[org.id]
    await orgStore.fetchOrganizations()
    await refreshServersForAllOrgs()
    ElMessage.success(`Deleted ${org.name}`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to delete organization'
    ElMessage.error(msg)
  }
}

onMounted(async () => {
  await orgStore.fetchOrganizations()
  await refreshServersForAllOrgs()
})

async function submitCreate() {
  if (!createFormRef.value) {
    return
  }
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  createSubmitting.value = true
  try {
    await orgStore.createOrganization({
      name: createForm.name.trim(),
      slug: createForm.slug.trim(),
    })
    await orgStore.fetchOrganizations()
    await refreshServersForAllOrgs()
    ElMessage.success('Organization created')
    showCreateDialog.value = false
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to create organization'
    ElMessage.error(msg)
  } finally {
    createSubmitting.value = false
  }
}

async function submitEdit() {
  if (!editFormRef.value || !editingOrgId.value) {
    return
  }
  try {
    await editFormRef.value.validate()
  } catch {
    return
  }
  editSubmitting.value = true
  try {
    await orgStore.updateOrganization(editingOrgId.value, {
      name: editForm.name.trim(),
      slug: editForm.slug.trim(),
    })
    await orgStore.fetchOrganizations()
    await loadServersForOrg(editingOrgId.value)
    ElMessage.success('Organization updated')
    showEditDialog.value = false
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to update organization'
    ElMessage.error(msg)
  } finally {
    editSubmitting.value = false
  }
}
</script>

<style scoped lang="scss">
.page-container {
  padding: 24px;
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.page-header__text {
  min-width: 0;
}

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
  margin: 0 0 8px;
}

.page-subtitle {
  margin: 0;
  font-size: 0.9375rem;
  color: #656a76;
  line-height: 1.5;
  max-width: 520px;
}

html.dark .page-title {
  color: #ffffff;
}

html.dark .page-subtitle {
  color: #b2b6bd;
}

.org-list-region {
  min-height: 140px;
}

.org-empty-wrap {
  padding: 32px 24px;
}

.org-cards {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.org-card {
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s ease;
}

.org-card:hover {
  box-shadow:
    0 1px 0 rgba(21, 24, 30, 0.04),
    0 10px 28px rgba(21, 24, 30, 0.07);
}

.org-card--current {
  border-color: rgba(20, 198, 203, 0.45);
  box-shadow:
    0 0 0 1px rgba(20, 198, 203, 0.2),
    0 6px 20px rgba(20, 198, 203, 0.08);
}

html.dark .org-card--current {
  border-color: rgba(20, 198, 203, 0.35);
}

.org-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 20px 16px;
}

.org-card__identity {
  display: flex;
  gap: 14px;
  min-width: 0;
  flex: 1;
}

.org-card__icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, rgba(20, 198, 203, 0.15), rgba(24, 104, 242, 0.12));
  color: #15181e;
}

html.dark .org-card__icon {
  color: #ffffff;
  background: linear-gradient(145deg, rgba(20, 198, 203, 0.2), rgba(24, 104, 242, 0.15));
}

.org-card__meta {
  min-width: 0;
}

.org-card__name {
  margin: 0 0 6px;
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.25;
  color: #000000;
  word-break: break-word;
}

html.dark .org-card__name {
  color: #ffffff;
}

.org-card__slug {
  margin: 0 0 10px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #656a76;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  word-break: break-all;
  line-height: 1.4;
}

html.dark .org-card__slug {
  color: #b2b6bd;
}

.org-card__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.org-card__date {
  font-size: 0.8125rem;
  color: #656a76;
}

html.dark .org-card__date {
  color: #b2b6bd;
}

.org-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.org-card__pop-wrap {
  display: inline-flex;
}

.org-card__action-btn {
  padding: 9px;
  min-height: auto;
  border-radius: 10px;
  border: 1px solid rgba(21, 24, 30, 0.12);
  background: #15181e;
  color: #ffffff;
}

.org-card__action-btn:hover {
  background: #0d0e12;
  color: #ffffff;
}

.org-card__action-btn--danger {
  border-color: rgba(115, 30, 37, 0.35);
  background: #731e25;
}

.org-card__action-btn--danger:hover {
  background: #5c181e;
  color: #ffffff;
}

html.dark .org-card__action-btn {
  background: #ffffff;
  color: #15181e;
  border-color: rgba(255, 255, 255, 0.2);
}

html.dark .org-card__action-btn:hover {
  background: #f1f2f3;
  color: #15181e;
}

html.dark .org-card__action-btn--danger {
  background: #731e25;
  color: #ffffff;
}

html.dark .org-card__action-btn--danger:hover {
  background: #5c181e;
  color: #ffffff;
}

.org-card__servers {
  border-top: 1px solid #e8e9eb;
  background: rgba(241, 242, 243, 0.55);
  padding: 16px 20px 20px;
}

html.dark .org-card__servers {
  border-top-color: rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.2);
}

.org-card__servers-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.org-card__servers-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #656a76;
}

html.dark .org-card__servers-title {
  color: #b2b6bd;
}

.servers-loading {
  padding: 8px 0;
}

.servers-empty {
  padding: 12px 0;
}

.servers-table-wrap {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e8e9eb;
  background: #ffffff;
}

html.dark .servers-table-wrap {
  border-color: rgba(255, 255, 255, 0.1);
  background: #15181e;
}

.servers-mini-table {
  width: 100%;
}

.servers-mini-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
</style>

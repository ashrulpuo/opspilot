<template>
  <div class="settings-container">
    <div class="page-header">
      <h1 class="page-title">Settings</h1>
      <p class="page-subtitle">Configure notifications and integrations</p>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- ── SMTP Tab ──────────────────────────────────────────────── -->
      <el-tab-pane label="Email (SMTP)" name="smtp">
        <div class="tab-section hc-card">
          <h2 class="section-title">SMTP Configuration</h2>
          <p class="section-desc">Configure outgoing email server for alert notifications.</p>

          <el-form
            ref="smtpFormRef"
            :model="smtpForm"
            :rules="smtpRules"
            label-width="140px"
            class="settings-form"
          >
            <el-form-item label="Enabled">
              <el-switch v-model="smtpForm.enabled" />
            </el-form-item>

            <el-form-item label="SMTP Host" prop="host">
              <el-input v-model="smtpForm.host" placeholder="smtp.gmail.com" />
            </el-form-item>

            <el-form-item label="Port" prop="port">
              <el-input-number v-model="smtpForm.port" :min="1" :max="65535" style="width: 160px" />
            </el-form-item>

            <el-form-item label="Username" prop="username">
              <el-input v-model="smtpForm.username" placeholder="your@email.com" />
            </el-form-item>

            <el-form-item label="Password">
              <el-input
                v-model="smtpForm.password"
                type="password"
                show-password
                :placeholder="smtpConfigSaved ? '(unchanged — leave blank to keep current)' : 'SMTP password'"
              />
            </el-form-item>

            <el-form-item label="From Address" prop="from_address">
              <el-input v-model="smtpForm.from_address" placeholder="OpsPilot <noreply@yourdomain.com>" />
            </el-form-item>

            <el-form-item label="Use TLS">
              <el-switch v-model="smtpForm.use_tls" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="smtpSaving" @click="saveSmtp">Save</el-button>
              <el-button :loading="smtpTesting" @click="showTestDialog = true" :disabled="!smtpConfigSaved">
                Send Test Email
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- ── Recipients Tab ───────────────────────────────────────── -->
      <el-tab-pane label="Notification Recipients" name="recipients">
        <div class="tab-section hc-card">
          <div class="section-header">
            <div>
              <h2 class="section-title">Notification Recipients</h2>
              <p class="section-desc">Email addresses that receive alert notifications.</p>
            </div>
            <el-button type="primary" @click="showAddRecipient = true">
              <el-icon><Plus /></el-icon>
              Add Recipient
            </el-button>
          </div>

          <el-table :data="recipients" v-loading="recipientsLoading" style="width: 100%; margin-top: 16px">
            <el-table-column prop="email" label="Email" min-width="200" />
            <el-table-column prop="name" label="Name" min-width="150">
              <template #default="{ row }">{{ row.name || '—' }}</template>
            </el-table-column>
            <el-table-column prop="severity_filter" label="Notify For" width="160">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="row.severity_filter === 'all' ? 'info' : row.severity_filter === 'critical' ? 'danger' : 'warning'"
                >
                  {{ row.severity_filter === 'all' ? 'All Alerts' : row.severity_filter === 'critical' ? 'Critical Only' : 'Warning & Critical' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="Status" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.enabled ? 'success' : 'info'">
                  {{ row.enabled ? 'Active' : 'Paused' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="120" fixed="right">
              <template #default="{ row }">
                <el-popconfirm title="Remove this recipient?" @confirm="deleteRecipient(row.id)">
                  <template #reference>
                    <el-button link type="danger" size="small">
                      <el-icon><Delete /></el-icon>
                      Remove
                    </el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!recipientsLoading && recipients.length === 0" description="No recipients yet" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Add Recipient Dialog -->
    <el-dialog v-model="showAddRecipient" title="Add Notification Recipient" width="480px" :close-on-click-modal="false">
      <el-form ref="recipientFormRef" :model="recipientForm" :rules="recipientRules" label-width="120px">
        <el-form-item label="Email" prop="email">
          <el-input v-model="recipientForm.email" placeholder="user@example.com" />
        </el-form-item>
        <el-form-item label="Name">
          <el-input v-model="recipientForm.name" placeholder="Optional display name" />
        </el-form-item>
        <el-form-item label="Notify For">
          <el-select v-model="recipientForm.severity_filter" style="width: 100%">
            <el-option label="All alerts" value="all" />
            <el-option label="Critical only" value="critical" />
            <el-option label="Warning & Critical" value="warning" />
          </el-select>
        </el-form-item>
        <el-form-item label="Enabled">
          <el-switch v-model="recipientForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRecipient = false">Cancel</el-button>
        <el-button type="primary" :loading="addingRecipient" @click="addRecipient">Add</el-button>
      </template>
    </el-dialog>

    <!-- Test Email Dialog -->
    <el-dialog v-model="showTestDialog" title="Send Test Email" width="400px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="Send To">
          <el-input v-model="testEmailAddress" placeholder="your@email.com" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTestDialog = false">Cancel</el-button>
        <el-button type="primary" :loading="smtpTesting" @click="sendTestEmail">Send</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import {
  NotificationSettingsAPI,
  type NotificationRecipient,
  type SmtpConfig,
} from '@/api/opspilot/notification_settings'

const activeTab = ref('smtp')

// ── SMTP ──────────────────────────────────────────────────────────────────────
const smtpFormRef = ref<FormInstance>()
const smtpSaving = ref(false)
const smtpTesting = ref(false)
const smtpConfigSaved = ref(false)
const showTestDialog = ref(false)
const testEmailAddress = ref('')

const smtpForm = reactive({
  host: '',
  port: 587,
  username: '',
  password: '',
  from_address: '',
  use_tls: true,
  enabled: true,
})

const smtpRules: FormRules = {
  host: [{ required: true, message: 'Enter SMTP host', trigger: 'blur' }],
  port: [{ required: true, message: 'Enter port', trigger: 'blur' }],
  username: [{ required: true, message: 'Enter username', trigger: 'blur' }],
  from_address: [{ required: true, message: 'Enter from address', trigger: 'blur' }],
}

const loadSmtpConfig = async () => {
  try {
    const config: SmtpConfig | null = await NotificationSettingsAPI.getSmtp()
    if (config) {
      smtpForm.host = config.host
      smtpForm.port = config.port
      smtpForm.username = config.username
      smtpForm.from_address = config.from_address
      smtpForm.use_tls = config.use_tls
      smtpForm.enabled = config.enabled
      smtpForm.password = ''
      smtpConfigSaved.value = true
    }
  } catch {
    // no config yet — form stays empty
  }
}

const saveSmtp = async () => {
  if (!smtpFormRef.value) return
  const valid = await smtpFormRef.value.validate().catch(() => false)
  if (!valid) return
  smtpSaving.value = true
  try {
    await NotificationSettingsAPI.saveSmtp(smtpForm)
    smtpConfigSaved.value = true
    ElMessage.success('SMTP configuration saved')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to save SMTP config')
  } finally {
    smtpSaving.value = false
  }
}

const sendTestEmail = async () => {
  if (!testEmailAddress.value) {
    ElMessage.warning('Enter an email address')
    return
  }
  smtpTesting.value = true
  try {
    const res = await NotificationSettingsAPI.testSmtp(testEmailAddress.value)
    ElMessage.success(res.message)
    showTestDialog.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'Test failed — check SMTP credentials')
  } finally {
    smtpTesting.value = false
  }
}

// ── Recipients ────────────────────────────────────────────────────────────────
const recipients = ref<NotificationRecipient[]>([])
const recipientsLoading = ref(false)
const showAddRecipient = ref(false)
const addingRecipient = ref(false)
const recipientFormRef = ref<FormInstance>()

const recipientForm = reactive({
  email: '',
  name: '',
  severity_filter: 'all',
  enabled: true,
})

const recipientRules: FormRules = {
  email: [
    { required: true, message: 'Enter email address', trigger: 'blur' },
    { type: 'email', message: 'Invalid email format', trigger: 'blur' },
  ],
}

const loadRecipients = async () => {
  recipientsLoading.value = true
  try {
    recipients.value = await NotificationSettingsAPI.listRecipients()
  } finally {
    recipientsLoading.value = false
  }
}

const addRecipient = async () => {
  if (!recipientFormRef.value) return
  const valid = await recipientFormRef.value.validate().catch(() => false)
  if (!valid) return
  addingRecipient.value = true
  try {
    const r = await NotificationSettingsAPI.addRecipient({
      email: recipientForm.email,
      name: recipientForm.name || undefined,
      severity_filter: recipientForm.severity_filter,
      enabled: recipientForm.enabled,
    })
    recipients.value.push(r)
    showAddRecipient.value = false
    recipientFormRef.value.resetFields()
    ElMessage.success('Recipient added')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to add recipient')
  } finally {
    addingRecipient.value = false
  }
}

const deleteRecipient = async (id: string) => {
  try {
    await NotificationSettingsAPI.deleteRecipient(id)
    recipients.value = recipients.value.filter(r => r.id !== id)
    ElMessage.success('Recipient removed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to remove recipient')
  }
}

onMounted(() => {
  loadSmtpConfig()
  loadRecipients()
})
</script>

<style scoped lang="scss">
.settings-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #000000;
    line-height: 1.2;
    margin: 0 0 8px 0;
  }

  .page-subtitle {
    font-size: 1rem;
    color: #656a76;
    margin: 0;
  }
}

html.dark .page-header {
  .page-title { color: #ffffff; }
  .page-subtitle { color: #d5d7db; }
}

.settings-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
}

.tab-section {
  padding: 24px;
  border-radius: 0 8px 8px 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #000000;
}

html.dark .section-title { color: #ffffff; }

.section-desc {
  font-size: 0.875rem;
  color: #656a76;
  margin: 0 0 20px 0;
}

html.dark .section-desc { color: #b2b6bd; }

.settings-form {
  max-width: 560px;
}
</style>

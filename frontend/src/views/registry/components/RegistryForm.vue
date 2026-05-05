<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? `Edit ${typeLabel}` : `Add ${typeLabel}`"
    width="540px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" label-position="top">

      <!-- Common: name -->
      <el-form-item label="Name" required>
        <el-input v-model="form.name" placeholder="e.g. Production DB" clearable />
      </el-form-item>

      <!-- Domain fields -->
      <template v-if="type === 'domains'">
        <el-form-item label="Registrar">
          <el-input v-model="form.registrar" placeholder="e.g. Namecheap" clearable />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Registered At">
              <el-date-picker v-model="form.registered_at" type="date" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Expires At">
              <el-date-picker v-model="form.expires_at" type="date" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="Auto-renew">
          <el-switch v-model="form.auto_renew" />
        </el-form-item>
        <el-form-item label="Nameservers">
          <el-input v-model="form.nameservers" placeholder="ns1.example.com, ns2.example.com" clearable />
        </el-form-item>
      </template>

      <!-- SSL cert fields -->
      <template v-if="type === 'ssl'">
        <el-form-item label="Domain Name" required>
          <el-input v-model="form.domain_name" placeholder="example.com" clearable />
        </el-form-item>
        <el-form-item label="Issuer">
          <el-input v-model="form.issuer" placeholder="e.g. Let's Encrypt" clearable />
        </el-form-item>
        <el-form-item label="Provider">
          <el-input v-model="form.provider" placeholder="e.g. Cloudflare" clearable />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Issued At">
              <el-date-picker v-model="form.issued_at" type="date" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Expires At">
              <el-date-picker v-model="form.expires_at" type="date" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="Auto-renew">
          <el-switch v-model="form.auto_renew" />
        </el-form-item>
      </template>

      <!-- DB service fields -->
      <template v-if="type === 'databases'">
        <el-form-item label="Database Type">
          <el-select v-model="form.db_type" style="width:100%">
            <el-option v-for="t in dbTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="Host" required>
              <el-input v-model="form.host" placeholder="db.example.com" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Port">
              <el-input-number v-model="form.port" :min="1" :max="65535" :controls="false" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Database Name">
              <el-input v-model="form.database_name" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Username">
              <el-input v-model="form.username" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="isEdit ? 'Password (leave blank to keep)' : 'Password'">
          <el-input v-model="form.password" type="password" show-password clearable />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Environment">
              <el-select v-model="form.environment" style="width:100%">
                <el-option label="Production" value="prod" />
                <el-option label="Staging" value="staging" />
                <el-option label="Development" value="dev" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="SSL">
              <el-switch v-model="form.ssl_enabled" active-text="Enabled" />
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- Credential fields -->
      <template v-if="type === 'credentials'">
        <el-form-item label="Type">
          <el-select v-model="form.credential_type" style="width:100%">
            <el-option label="Web Login" value="web_login" />
            <el-option label="API Key" value="api_key" />
            <el-option label="Token" value="token" />
            <el-option label="SMTP" value="smtp" />
            <el-option label="FTP" value="ftp" />
            <el-option label="Other" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="form.url" placeholder="https://app.example.com" clearable />
        </el-form-item>
        <el-form-item label="Username">
          <el-input v-model="form.username" clearable />
        </el-form-item>
        <el-form-item :label="isEdit ? 'Secret (leave blank to keep)' : 'Secret'">
          <el-input v-model="form.secret" type="password" show-password clearable />
        </el-form-item>
        <el-form-item label="Environment">
          <el-select v-model="form.environment" style="width:100%">
            <el-option label="Production" value="prod" />
            <el-option label="Staging" value="staging" />
            <el-option label="Development" value="dev" />
          </el-select>
        </el-form-item>
      </template>

      <!-- Common: notes -->
      <el-form-item label="Notes">
        <el-input v-model="form.notes" type="textarea" :rows="2" clearable />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">Cancel</el-button>
      <el-button type="primary" :loading="saving" @click="submit">
        {{ isEdit ? 'Save Changes' : `Add ${typeLabel}` }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  type: string
  item?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  submit: [data: Record<string, unknown>]
}>()

const visible = computed({ get: () => props.modelValue, set: v => emit('update:modelValue', v) })
const isEdit = computed(() => !!props.item)
const saving = ref(false)

const typeLabel = computed(() => ({
  domains: 'Domain', ssl: 'SSL Cert', databases: 'Database', credentials: 'Credential',
}[props.type] ?? 'Asset'))

const dbTypes = ['postgres', 'mysql', 'mariadb', 'redis', 'mongodb', 'sqlite', 'other']

const defaultForm = () => ({
  name: '', registrar: '', registered_at: null, expires_at: null, auto_renew: false,
  nameservers: '', domain_name: '', issuer: '', provider: '', issued_at: null,
  fingerprint: '', db_type: 'postgres', host: '', port: undefined as number | undefined,
  database_name: '', username: '', password: '', environment: 'prod', ssl_enabled: false,
  credential_type: 'web_login', url: '', secret: '', notes: '',
})

const form = ref(defaultForm())

watch(() => props.item, (item) => {
  if (item) {
    form.value = { ...defaultForm(), ...item, password: '', secret: '' }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

async function submit() {
  saving.value = true
  try {
    const data: Record<string, unknown> = { ...form.value }
    if (!data.password) delete data.password
    if (!data.secret) delete data.secret
    emit('submit', data)
    visible.value = false
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? 'Edit Monitor' : 'Add Monitor'"
    width="520px"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="monitor-form"
    >
      <el-form-item label="Name" prop="name">
        <el-input v-model="form.name" placeholder="e.g. Production API" clearable />
      </el-form-item>

      <el-form-item label="Type" prop="type">
        <el-segmented v-model="form.type" :options="typeOptions" class="type-seg" />
      </el-form-item>

      <template v-if="form.type !== 'push'">
        <el-form-item :label="urlLabel" prop="url">
          <el-input
            v-model="form.url"
            :placeholder="urlPlaceholder"
            clearable
          >
            <template v-if="form.type === 'tcp'" #append>
              <el-input-number
                v-model="form.port"
                :min="1"
                :max="65535"
                :controls="false"
                placeholder="Port"
                style="width: 80px"
              />
            </template>
          </el-input>
        </el-form-item>
      </template>

      <template v-if="form.type === 'push'">
        <el-alert
          v-if="isEdit && monitor?.heartbeat_api_key"
          type="info"
          :closable="false"
          class="push-info"
        >
          <template #title>Heartbeat URL</template>
          <div class="push-url-row">
            <code class="push-url">{{ heartbeatUrl }}</code>
            <el-button size="small" @click="copyHeartbeatUrl">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
        </el-alert>
        <el-alert
          v-else-if="!isEdit"
          type="info"
          :closable="false"
          class="push-info"
          title="After creating, you'll receive a unique heartbeat URL to call from your service."
        />
      </template>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="Check Interval" prop="interval_seconds">
            <el-select v-model="form.interval_seconds" style="width: 100%">
              <el-option label="1 minute" :value="60" />
              <el-option label="5 minutes" :value="300" />
              <el-option label="15 minutes" :value="900" />
              <el-option label="30 minutes" :value="1800" />
              <el-option label="1 hour" :value="3600" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Timeout" prop="timeout_seconds">
            <el-select v-model="form.timeout_seconds" style="width: 100%">
              <el-option label="5 seconds" :value="5" />
              <el-option label="10 seconds" :value="10" />
              <el-option label="20 seconds" :value="20" />
              <el-option label="30 seconds" :value="30" />
              <el-option label="60 seconds" :value="60" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <template v-if="form.type === 'dns'">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-form-item label="DNS Record Type">
              <el-select v-model="form.dns_resolve_type" style="width: 100%">
                <el-option label="A" value="A" />
                <el-option label="CNAME" value="CNAME" />
                <el-option label="MX" value="MX" />
                <el-option label="TXT" value="TXT" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="14">
            <el-form-item label="Expected Value (optional)">
              <el-input v-model="form.dns_resolve_expected" placeholder="e.g. 1.2.3.4" clearable />
            </el-form-item>
          </el-col>
        </el-row>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ isEdit ? 'Save Changes' : 'Add Monitor' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Monitor, CreateMonitorRequest } from '@/api/opspilot/monitors'

const props = defineProps<{
  modelValue: boolean
  monitor?: Monitor | null
}>()

const emit = defineEmits<{
  'update:modelValue': [val: boolean]
  submit: [data: CreateMonitorRequest]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.monitor)
const formRef = ref<FormInstance>()
const loading = ref(false)

interface FormData extends CreateMonitorRequest {
  dns_resolve_type?: string
  dns_resolve_expected?: string
}

const defaultForm = (): FormData => ({
  name: '',
  url: '',
  type: 'https',
  port: undefined,
  interval_seconds: 300,
  timeout_seconds: 10,
  dns_resolve_type: 'A',
  dns_resolve_expected: '',
})

const form = ref<FormData>(defaultForm())

watch(() => props.monitor, (m) => {
  if (m) {
    form.value = {
      name: m.name,
      url: m.url,
      type: m.type,
      port: m.port,
      interval_seconds: m.interval_seconds,
      timeout_seconds: m.timeout_seconds,
      dns_resolve_type: 'A',
      dns_resolve_expected: '',
    }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

const typeOptions = [
  { label: 'HTTPS', value: 'https' },
  { label: 'HTTP', value: 'http' },
  { label: 'TCP', value: 'tcp' },
  { label: 'DNS', value: 'dns' },
  { label: 'Push', value: 'push' },
]

const urlLabel = computed(() => ({
  http: 'URL', https: 'URL', tcp: 'Host', dns: 'Hostname',
}[form.value.type] ?? 'URL'))

const urlPlaceholder = computed(() => ({
  http: 'http://example.com',
  https: 'https://example.com/api/health',
  tcp: 'db.example.com',
  dns: 'example.com',
}[form.value.type] ?? ''))

const heartbeatUrl = computed(() => {
  const origin = window.location.origin
  return `${origin}/api/v1/monitors/${props.monitor?.id}/heartbeat?api_key=${props.monitor?.heartbeat_api_key}`
})

const rules: FormRules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
  url: [
    {
      validator: (_rule, _value, cb) => {
        if (form.value.type === 'push') return cb()
        if (!form.value.url) return cb(new Error('URL / Host is required'))
        cb()
      },
      trigger: 'blur',
    },
  ],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    emit('submit', { ...form.value })
    visible.value = false
  } finally {
    loading.value = false
  }
}

function handleClose() {
  formRef.value?.clearValidate()
  form.value = defaultForm()
  visible.value = false
}

async function copyHeartbeatUrl() {
  await navigator.clipboard.writeText(heartbeatUrl.value)
  ElMessage.success('Copied to clipboard')
}
</script>

<style scoped>
.monitor-form {
  padding: 4px 0;
}

.type-seg {
  width: 100%;
}

.push-info {
  margin-bottom: 18px;
}

.push-url-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.push-url {
  font-size: 11px;
  background: var(--el-fill-color);
  padding: 4px 8px;
  border-radius: 4px;
  word-break: break-all;
  flex: 1;
}
</style>

<template>
  <div class="setup-container">
    <div class="setup-box">
      <div class="setup-left">
        <div class="brand">
          <h1 class="brand-title">OpsPilot</h1>
          <p class="brand-subtitle">Create the administrator account for this installation</p>
        </div>
      </div>

      <div class="setup-form">
        <div class="form-header">
          <h2 class="form-title">Initial setup</h2>
          <p class="form-subtitle">This runs once on a fresh database</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          class="setup-form-content"
          label-position="top"
          @submit.prevent="submit"
        >
          <el-form-item label="Username (display name)" prop="full_name">
            <el-input
              v-model="form.full_name"
              placeholder="Your name"
              size="large"
              :prefix-icon="User"
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item label="Email" prop="email">
            <el-input
              v-model="form.email"
              placeholder="admin@example.com"
              size="large"
              :prefix-icon="Message"
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item label="Password" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="At least 8 characters"
              size="large"
              :prefix-icon="Lock"
              :disabled="loading"
              show-password
            />
          </el-form-item>

          <el-form-item label="Confirm password" prop="confirm_password">
            <el-input
              v-model="form.confirm_password"
              type="password"
              placeholder="Repeat password"
              size="large"
              :prefix-icon="Lock"
              :disabled="loading"
              show-password
              @keyup.enter="submit"
            />
          </el-form-item>

          <div class="setup-actions">
            <el-button :disabled="loading" @click="fillRandomPassword"> Generate random password </el-button>
            <el-button v-if="form.password" :disabled="loading" link type="primary" @click="copyPassword">
              Copy password
            </el-button>
          </div>

          <el-button type="primary" size="large" class="submit-button" :loading="loading" @click="submit">
            {{ loading ? 'Creating account…' : 'Complete setup' }}
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'
import axios from 'axios'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'

const router = useRouter()
const authStore = useOpsPilotAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  full_name: '',
  email: '',
  password: '',
  confirm_password: '',
})

const validateConfirm = (rule: unknown, value: string, callback: (e?: Error) => void) => {
  if (value !== form.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  full_name: [
    { required: true, message: 'Please enter a username', trigger: 'blur' },
    { min: 2, message: 'Use at least 2 characters', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Please enter a password', trigger: 'blur' },
    { min: 8, message: 'Password must be at least 8 characters', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: 'Please confirm your password', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

const RANDOM_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*-_'

function generateRandomPassword(length = 22): string {
  const bytes = new Uint8Array(length)
  crypto.getRandomValues(bytes)
  let out = ''
  for (let i = 0; i < length; i += 1) {
    out += RANDOM_CHARS[bytes[i]! % RANDOM_CHARS.length]
  }
  return out
}

function fillRandomPassword() {
  const pwd = generateRandomPassword()
  form.password = pwd
  form.confirm_password = pwd
  ElMessage.success('Random password filled in both fields')
}

async function copyPassword() {
  try {
    await navigator.clipboard.writeText(form.password)
    ElMessage.success('Copied to clipboard')
  } catch {
    ElMessage.error('Could not copy')
  }
}

function setupErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    if (status === 404) {
      return 'The API returned 404. Set VITE_API_URL to your OpsPilot backend origin (e.g. http://127.0.0.1:8000) with no /api/v1 suffix, ensure the server is running, then restart the dev server.'
    }
    if (status === 403) {
      return 'Initial setup is not allowed (for example, a user already exists). Use a fresh database or sign in instead.'
    }
    const detail = error.response?.data && (error.response.data as { detail?: unknown }).detail
    if (typeof detail === 'string') {
      return detail
    }
  }
  const err = error as { message?: string }
  return err.message || 'Setup failed. Try again.'
}

async function submit() {
  if (!formRef.value) {
    return
  }
  try {
    await formRef.value.validate()
    loading.value = true
    await authStore.bootstrapFirstAdmin({
      full_name: form.full_name,
      email: form.email,
      password: form.password,
      confirm_password: form.confirm_password,
    })
    ElMessage.success('Setup complete')
    await router.replace('/dashboard')
  } catch (error: unknown) {
    console.error(error)
    ElMessage.error(setupErrorMessage(error))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.setup-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f2f3 0%, #d5d7db 100%);
  padding: 20px;
}

.setup-box {
  display: flex;
  width: 100%;
  max-width: 960px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow:
    0 4px 6px rgba(0, 0, 0, 0.05),
    0 10px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.setup-left {
  flex: 0 0 38%;
  padding: 40px 32px;
  background: linear-gradient(165deg, #15181e 0%, #1e232b 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}

.brand-subtitle {
  margin: 0;
  opacity: 0.85;
  font-size: 14px;
  line-height: 1.5;
}

.setup-form {
  flex: 1;
  padding: 40px 40px 48px;
}

.form-header {
  margin-bottom: 24px;
}

.form-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 6px;
  color: #1e232b;
}

.form-subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.setup-form-content {
  max-width: 420px;
}

.setup-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.submit-button {
  width: 100%;
}

@media (max-width: 768px) {
  .setup-box {
    flex-direction: column;
  }

  .setup-left {
    flex: none;
    padding: 28px 24px;
  }
}
</style>

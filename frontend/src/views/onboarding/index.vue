<template>
  <div class="onboarding-container">
    <!-- Progress Steps -->
    <div class="progress-steps">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="Organization" />
        <el-step title="First server" />
        <el-step title="Done" />
      </el-steps>
    </div>

    <!-- Step 0: Create Organization (skip if bootstrap already created one) -->
    <div v-show="currentStep === 0" class="step-content">
      <div class="step-header">
        <h2 class="step-title">Create your organization</h2>
        <p class="step-subtitle">Optional if you already have one from initial setup — otherwise create one here</p>
      </div>

      <el-form
        ref="orgFormRef"
        :model="orgForm"
        :rules="orgRules"
        class="onboarding-form"
        @submit.prevent="handleOrgSubmit"
      >
        <el-form-item label="Organization Name" prop="name">
          <el-input
            v-model="orgForm.name"
            placeholder="My Company"
            size="large"
            :prefix-icon="OfficeBuilding"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item label="Slug (URL-friendly name)" prop="slug">
          <el-input
            v-model="orgForm.slug"
            placeholder="my-company"
            size="large"
            :prefix-icon="Link"
            :disabled="loading"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="onboarding-button"
          :loading="loading"
          @click="handleOrgSubmit"
        >
          Continue
        </el-button>
      </el-form>

      <div class="step-footer">
        <span class="footer-text">Accounts are not self-registered — use initial setup on a new install.</span>
      </div>
    </div>

    <!-- Step 1: Add First Server -->
    <div v-show="currentStep === 1" class="step-content">
      <div class="step-header">
        <h2 class="step-title">Add Your First Server</h2>
        <p class="step-subtitle">Connect your first server to start monitoring</p>
      </div>

      <el-form
        ref="serverFormRef"
        :model="serverForm"
        :rules="serverRules"
        class="onboarding-form"
        @submit.prevent="handleServerSubmit"
      >
        <el-form-item label="Hostname" prop="hostname">
          <el-input
            v-model="serverForm.hostname"
            placeholder="web-server-01"
            size="large"
            :prefix-icon="Monitor"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item label="IP Address" prop="ip_address">
          <el-input
            v-model="serverForm.ip_address"
            placeholder="192.168.1.100"
            size="large"
            :prefix-icon="Connection"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item label="OS Type" prop="os_type">
          <el-select
            v-model="serverForm.os_type"
            placeholder="Select operating system"
            size="large"
            :disabled="loading"
            style="width: 100%"
          >
            <el-option label="Linux" value="linux" />
            <el-option label="macOS" value="macos" />
            <el-option label="Windows" value="windows" />
          </el-select>
        </el-form-item>

        <el-form-item label="Domain (Optional)">
          <el-input
            v-model="serverForm.domain_name"
            placeholder="example.com"
            size="large"
            :prefix-icon="Link"
            :disabled="loading"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="onboarding-button"
          :loading="loading"
          @click="handleServerSubmit"
        >
          Continue
        </el-button>
      </el-form>

      <div class="step-footer">
        <el-button link @click="previousStep">
          <el-icon><ArrowLeft /></el-icon>
          Back
        </el-button>
      </div>
    </div>

    <!-- Step 2: Complete -->
    <div v-show="currentStep === 2" class="step-content">
      <div class="complete-container">
        <div class="complete-icon">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="complete-content">
          <h2 class="complete-title">You're All Set! 🎉</h2>
          <p class="complete-subtitle">
            Your OpsPilot account is ready. You can now start monitoring your servers.
          </p>
          <ul class="feature-list">
            <li>
              <el-icon><Monitor /></el-icon>
              <span>Real-time server monitoring</span>
            </li>
            <li>
              <el-icon><Bell /></el-icon>
              <span>Smart alerts and notifications</span>
            </li>
            <li>
              <el-icon><Operation /></el-icon>
              <span>Execute commands remotely</span>
            </li>
            <li>
              <el-icon><DataAnalysis /></el-icon>
              <span>Track metrics and performance</span>
            </li>
          </ul>
          <el-button
            type="primary"
            size="large"
            class="complete-button"
            @click="goToDashboard"
          >
            Go to Dashboard
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { OfficeBuilding, Monitor, Connection, Link, ArrowLeft, CircleCheck, Bell, Operation, DataAnalysis } from '@element-plus/icons-vue'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'
import { OrganizationsAPI } from '@/api/opspilot/organizations'

const router = useRouter()
const authStore = useOpsPilotAuthStore()
const orgStore = useOpsPilotOrganizationStore()

const currentStep = ref(0)
const loading = ref(false)

// Form refs
const orgFormRef = ref<FormInstance>()
const serverFormRef = ref<FormInstance>()

// Organization form data
const orgForm = reactive({
  name: '',
  slug: '',
})

// Server form data
const serverForm = reactive({
  hostname: '',
  ip_address: '',
  os_type: 'linux' as 'linux' | 'macos' | 'windows',
  domain_name: '',
})

// Organization form rules
const orgRules: FormRules = {
  name: [
    { required: true, message: 'Please enter organization name', trigger: 'blur' },
    { min: 2, message: 'Name must be at least 2 characters', trigger: 'blur' },
  ],
  slug: [
    { required: true, message: 'Please enter a slug', trigger: 'blur' },
    {
      pattern: /^[a-z0-9-]+$/,
      message: 'Slug can only contain lowercase letters, numbers, and hyphens',
      trigger: 'blur',
    },
  ],
}

// Server form rules
const serverRules: FormRules = {
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

// Navigation methods
const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const nextStep = () => {
  if (currentStep.value < 2) {
    currentStep.value++
  }
}

onMounted(async () => {
  try {
    await orgStore.fetchOrganizations()
    if (orgStore.organizations.length > 0) {
      currentStep.value = 1
    }
  } catch {
    /* stay on org step */
  }
})

// Step 0: Create Organization
const handleOrgSubmit = async () => {
  if (!orgFormRef.value) return

  try {
    const valid = await orgFormRef.value.validate()
    if (!valid) return

    loading.value = true

    // Create organization
    await orgStore.createOrganization({
      name: orgForm.name,
      slug: orgForm.slug,
    })

    ElMessage.success('Organization created successfully')
    nextStep()
  } catch (error: any) {
    ElMessage.error(error.message || 'Failed to create organization')
  } finally {
    loading.value = false
  }
}

// Step 1: Add First Server
const handleServerSubmit = async () => {
  if (!serverFormRef.value) return

  try {
    const valid = await serverFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const orgId =
      orgStore.currentOrganization?.id || orgStore.organizations[0]?.id || authStore.user?.organizations?.[0]?.id
    if (!orgId) {
      ElMessage.error('No organization found. Create an organization first.')
      return
    }

    await OrganizationsAPI.createServer(orgId, {
      hostname: serverForm.hostname,
      ip_address: serverForm.ip_address,
      os_type: serverForm.os_type,
      domain_name: serverForm.domain_name || undefined,
    })

    ElMessage.success('Server added successfully')
    nextStep()
  } catch (error: any) {
    ElMessage.error(error.message || 'Failed to add server')
  } finally {
    loading.value = false
  }
}

// Step 2: Complete
const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped lang="scss">
.onboarding-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f2f3 0%, #d5d7db 100%);
  padding: 20px;
}

.progress-steps {
  max-width: 800px;
  margin: 0 auto 40px;
  text-align: center;
}

.step-content {
  max-width: 700px;
  margin: 0 auto;
}

.step-header {
  text-align: center;
  margin-bottom: 40px;

  .step-title {
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
    margin: 0 0 16px 0;
  }

  .step-subtitle {
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

.onboarding-form {
  background: #ffffff;
  padding: 40px;
  border-radius: 8px;
  box-shadow:
    0 4px 12px rgba(97, 104, 117, 0.1),
    0 2px 4px rgba(97, 104, 117, 0.05);
}

.onboarding-button {
  width: 100%;
  height: 44px;
  border-radius: 5px;
  font-weight: 600;
  font-size: 1rem;
  background: #15181e;
  border-color: rgba(178, 182, 189, 0.4);
  color: #ffffff;

  &:hover {
    background: #0d0e12;
    border-color: rgba(178, 182, 189, 0.4);
  }

  &:disabled {
    background: #d5d7db;
    color: #656a76;
  }
}

.step-footer {
  display: flex;
  justify-content: center;
  margin-top: 24px;

  .footer-text {
    font-size: 0.875rem;
    color: #656a76;
    margin-right: 8px;
  }

  .footer-link {
    font-size: 0.875rem;
    color: #2264d6;
    text-decoration: none;
    font-weight: 500;

    &:hover {
      color: #15181e;
      text-decoration: underline;
    }
  }
}

.complete-container {
  display: flex;
  align-items: center;
  gap: 40px;
  padding: 60px;
  max-width: 700px;
  margin: 0 auto;
}

.complete-icon {
  font-size: 64px;
  color: #14c6cb;
}

.complete-content {
  flex: 1;
  text-align: center;

  .complete-title {
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
    margin: 0 0 24px 0;
  }

  .complete-subtitle {
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
    margin: 0 0 32px 0;
  }
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 40px 0;

  li {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    font-size: 0.9375rem;
    color: #656a76;
  }
}

.complete-button {
  width: 100%;
  height: 48px;
  border-radius: 5px;
  font-weight: 600;
  font-size: 1rem;
  background: #15181e;
  border-color: rgba(178, 182, 189, 0.4);
  color: #ffffff;
  margin-top: 32px;

  &:hover {
    background: #0d0e12;
    border-color: rgba(178, 182, 189, 0.4);
  }
}

html.dark .onboarding-container {
  background: linear-gradient(135deg, #0d0e12 0%, #15181e 100%);
}

html.dark .onboarding-form {
  background: #0d0e12;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.1),
    0 2px 4px rgba(0, 0, 0, 0.05);
}

html.dark .step-header .step-title {
  color: #ffffff;
}

html.dark .step-header .step-subtitle {
  color: #b2b6bd;
}

html.dark .step-footer .footer-text {
  color: #b2b6bd;
}

html.dark .complete-content .complete-title {
  color: #ffffff;
}

html.dark .complete-content .complete-subtitle {
  color: #b2b6bd;
}

html.dark .feature-list li {
  color: #b2b6bd;
}

html.dark .onboarding-button {
  background: #0d0e12;
  border-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;

  &:hover {
    background: #15181e;
    border-color: rgba(255, 255, 255, 0.2);
  }

  &:disabled {
    background: #1e293b;
    color: #656a76;
  }
}

// Responsive design
@media (max-width: 768px) {
  .onboarding-container {
    padding: 10px;
  }

  .progress-steps {
    margin: 0 auto 20px;
  }

  .step-content {
    max-width: 500px;
  }

  .onboarding-form {
    padding: 24px;
  }

  .complete-container {
    flex-direction: column;
    padding: 30px;
  }
}
</style>

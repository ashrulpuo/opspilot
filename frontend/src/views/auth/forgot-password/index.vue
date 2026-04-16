<template>
  <div class="forgot-password-container">
    <div class="forgot-password-box">
      <div class="form-header">
        <div class="logo">
          <h1 class="logo-title">OpsPilot</h1>
        </div>
        <h2 class="form-title">Forgot your password?</h2>
        <p class="form-subtitle">Enter your email address and we'll send you a link to reset your password</p>
      </div>

      <el-form
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        class="forgot-form-content"
        @submit.prevent="handleForgotPassword"
      >
        <el-form-item prop="email">
          <el-input
            v-model="forgotForm.email"
            placeholder="Email address"
            size="large"
            :prefix-icon="Message"
            :disabled="loading"
          />
        </el-form-item>

        <el-button type="primary" size="large" class="submit-button" :loading="loading" @click="handleForgotPassword">
          {{ loading ? 'Sending...' : 'Send reset link' }}
        </el-button>

        <div class="form-footer">
          <router-link to="/login" class="back-link">
            <el-icon><ArrowLeft /></el-icon>
            Back to login
          </router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message, ArrowLeft } from '@element-plus/icons-vue'
import { AuthAPI } from '@/api/opspilot/auth'

const router = useRouter()

const forgotFormRef = ref<FormInstance>()
const loading = ref(false)

const forgotForm = reactive({
  email: '',
})

const forgotRules: FormRules = {
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' },
  ],
}

const handleForgotPassword = async () => {
  if (!forgotFormRef.value) return

  try {
    const valid = await forgotFormRef.value.validate()
    if (!valid) return

    loading.value = true

    await AuthAPI.forgotPassword({
      email: forgotForm.email,
    })

    ElMessage.success('Password reset link sent to your email')
    await router.push('/login')
  } catch (error: any) {
    console.error('Forgot password error:', error)
    ElMessage.error(error.message || 'Failed to send reset link. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.forgot-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f2f3 0%, #d5d7db 100%);
  padding: 20px;

  .forgot-password-box {
    width: 100%;
    max-width: 480px;
    background: #ffffff;
    border-radius: 8px;
    box-shadow:
      rgba(97, 104, 117, 0.1) 0px 4px 12px,
      rgba(97, 104, 117, 0.05) 0px 2px 4px;
    padding: 48px;
  }

  .form-header {
    text-align: center;
    margin-bottom: 40px;

    .logo {
      margin-bottom: 24px;

      .logo-title {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #15181e;
        line-height: 1.2;
        margin: 0;
      }
    }

    .form-title {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1.5rem;
      font-weight: 600;
      color: #000000;
      line-height: 1.3;
      margin: 0 0 12px 0;
    }

    .form-subtitle {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.9375rem;
      font-weight: 400;
      color: #656a76;
      line-height: 1.6;
      margin: 0;
    }
  }

  .forgot-form-content {
    :deep(.el-form-item) {
      margin-bottom: 24px;
    }

    :deep(.el-input) {
      .el-input__wrapper {
        border-radius: 5px;
        padding: 11px 15px;
      }
    }
  }

  .submit-button {
    width: 100%;
    height: 44px;
    border-radius: 5px;
    font-weight: 600;
    font-size: 1rem;
    background: #15181e;
    border-color: rgba(178, 182, 189, 0.4);
    color: #d5d7db;
    margin-bottom: 24px;

    &:hover {
      background: #0d0e12;
      border-color: rgba(178, 182, 189, 0.4);
    }
  }

  .form-footer {
    text-align: center;

    .back-link {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.875rem;
      color: #2264d6;
      text-decoration: none;
      font-weight: 500;

      &:hover {
        color: #2b89ff;
        text-decoration: underline;
      }
    }
  }
}

html.dark .forgot-password-container {
  background: linear-gradient(135deg, #0d0e12 0%, #15181e 100%);

  .forgot-password-box {
    background: #15181e;
    border: 1px solid rgba(178, 182, 189, 0.4);
  }

  .form-header {
    .logo .logo-title {
      color: #ffffff;
    }

    .form-title {
      color: #ffffff;
    }

    .form-subtitle {
      color: #d5d7db;
    }
  }
}

// Responsive design
@media (max-width: 768px) {
  .forgot-password-container .forgot-password-box {
    padding: 32px 24px;
  }
}
</style>

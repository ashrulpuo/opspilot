<template>
  <div class="register-container">
    <div class="register-box">
      <!-- Left side - Logo and branding -->
      <div class="register-left">
        <div class="brand">
          <h1 class="brand-title">OpsPilot</h1>
          <p class="brand-subtitle">Start monitoring your servers in minutes</p>
        </div>
        <div class="features">
          <div class="feature">
            <div class="feature-icon">📊</div>
            <div class="feature-text">
              <h3>Real-time Monitoring</h3>
              <p>Track server metrics instantly</p>
            </div>
          </div>
          <div class="feature">
            <div class="feature-icon">🔔</div>
            <div class="feature-text">
              <h3>Smart Alerts</h3>
              <p>Get notified before issues occur</p>
            </div>
          </div>
          <div class="feature">
            <div class="feature-icon">⚡</div>
            <div class="feature-text">
              <h3>Quick Actions</h3>
              <p>Execute commands remotely</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side - Register form -->
      <div class="register-form">
        <div class="form-header">
          <h2 class="form-title">Create your account</h2>
          <p class="form-subtitle">Start your free trial today</p>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="register-form-content"
          @submit.prevent="handleRegister"
        >
          <el-form-item prop="full_name">
            <el-input
              v-model="registerForm.full_name"
              placeholder="Full name"
              size="large"
              :prefix-icon="User"
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="Email address"
              size="large"
              :prefix-icon="Message"
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="Password"
              size="large"
              :prefix-icon="Lock"
              :disabled="loading"
              show-password
            />
          </el-form-item>

          <el-form-item prop="confirm_password">
            <el-input
              v-model="registerForm.confirm_password"
              type="password"
              placeholder="Confirm password"
              size="large"
              :prefix-icon="Lock"
              :disabled="loading"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <div class="terms-agreement">
            <el-checkbox v-model="agreeTerms">
              I agree to the
              <a href="#" class="terms-link">Terms of Service</a>
              and
              <a href="#" class="terms-link">Privacy Policy</a>
            </el-checkbox>
          </div>

          <el-button
            type="primary"
            size="large"
            class="register-button"
            :loading="loading"
            :disabled="!agreeTerms"
            @click="handleRegister"
          >
            {{ loading ? 'Creating account...' : 'Create account' }}
          </el-button>

          <div class="form-footer">
            <span class="footer-text">Already have an account?</span>
            <router-link to="/login" class="login-link">Sign in</router-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message, Lock, User } from '@element-plus/icons-vue'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'

const router = useRouter()
const authStore = useOpsPilotAuthStore()

const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const agreeTerms = ref(false)

const registerForm = reactive({
  full_name: '',
  email: '',
  password: '',
  confirm_password: '',
})

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  full_name: [
    { required: true, message: 'Please enter your full name', trigger: 'blur' },
    { min: 2, message: 'Name must be at least 2 characters', trigger: 'blur' },
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
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    if (!agreeTerms.value) {
      ElMessage.warning('Please agree to the terms and conditions')
      return
    }

    loading.value = true

    await authStore.register({
      full_name: registerForm.full_name,
      email: registerForm.email,
      password: registerForm.password,
      confirm_password: registerForm.confirm_password,
    })

    ElMessage.success('Account created successfully')
    await router.push('/onboarding')
  } catch (error: any) {
    console.error('Registration error:', error)
    ElMessage.error(error.message || 'Registration failed. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f2f3 0%, #d5d7db 100%);
  padding: 20px;

  .register-box {
    display: flex;
    width: 100%;
    max-width: 1100px;
    background: #ffffff;
    border-radius: 8px;
    box-shadow:
      rgba(97, 104, 117, 0.1) 0px 4px 12px,
      rgba(97, 104, 117, 0.05) 0px 2px 4px;
    overflow: hidden;
  }

  .register-left {
    flex: 1;
    padding: 60px;
    background: #15181e;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: flex-start;

    .brand {
      .brand-title {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        margin: 0 0 12px 0;
      }

      .brand-subtitle {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 1rem;
        font-weight: 400;
        color: #d5d7db;
        line-height: 1.5;
        margin: 0;
      }
    }

    .features {
      display: flex;
      flex-direction: column;
      gap: 24px;

      .feature {
        display: flex;
        align-items: flex-start;
        gap: 16px;

        .feature-icon {
          font-size: 1.5rem;
          flex-shrink: 0;
        }

        .feature-text {
          h3 {
            font-family:
              system-ui,
              -apple-system,
              BlinkMacSystemFont,
              'Segoe UI',
              sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: #ffffff;
            line-height: 1.4;
            margin: 0 0 4px 0;
          }

          p {
            font-family:
              system-ui,
              -apple-system,
              BlinkMacSystemFont,
              'Segoe UI',
              sans-serif;
            font-size: 0.875rem;
            font-weight: 400;
            color: #b2b6bd;
            line-height: 1.5;
            margin: 0;
          }
        }
      }
    }
  }

  .register-form {
    flex: 1;
    padding: 60px;
    display: flex;
    flex-direction: column;
    justify-content: center;

    .form-header {
      margin-bottom: 40px;

      .form-title {
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

      .form-subtitle {
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

    .register-form-content {
      :deep(.el-form-item) {
        margin-bottom: 20px;
      }

      :deep(.el-input) {
        .el-input__wrapper {
          border-radius: 5px;
          padding: 11px 15px;
        }
      }
    }

    .terms-agreement {
      margin-bottom: 24px;

      :deep(.el-checkbox) {
        .el-checkbox__label {
          font-size: 0.875rem;
          color: #656a76;
        }
      }

      .terms-link {
        color: #2264d6;
        text-decoration: none;

        &:hover {
          color: #2b89ff;
          text-decoration: underline;
        }
      }
    }

    .register-button {
      width: 100%;
      height: 44px;
      border-radius: 5px;
      font-weight: 600;
      font-size: 1rem;
      background: #15181e;
      border-color: rgba(178, 182, 189, 0.4);
      color: #d5d7db;

      &:hover {
        background: #0d0e12;
        border-color: rgba(178, 182, 189, 0.4);
      }

      &:disabled {
        background: #d5d7db;
        color: #656a76;
      }
    }

    .form-footer {
      margin-top: 24px;
      text-align: center;

      .footer-text {
        font-size: 0.875rem;
        color: #656a76;
        margin-right: 8px;
      }

      .login-link {
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
}

html.dark .register-container {
  background: linear-gradient(135deg, #0d0e12 0%, #15181e 100%);

  .register-box {
    background: #15181e;
    border: 1px solid rgba(178, 182, 189, 0.4);
  }

  .register-form {
    .form-header {
      .form-title {
        color: #ffffff;
      }

      .form-subtitle {
        color: #d5d7db;
      }
    }

    .terms-agreement {
      :deep(.el-checkbox) {
        .el-checkbox__label {
          color: #b2b6bd;
        }
      }
    }

    .form-footer {
      .footer-text {
        color: #b2b6bd;
      }
    }
  }
}

// Responsive design
@media (max-width: 768px) {
  .register-container .register-box {
    flex-direction: column;
    max-width: 500px;
  }

  .register-container .register-left {
    padding: 40px;
  }

  .register-container .register-form {
    padding: 40px;
  }
}
</style>

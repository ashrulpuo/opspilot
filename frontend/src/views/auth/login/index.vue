<template>
  <div class="login-container">
    <div class="login-box">
      <!-- Left side - Logo and branding -->
      <div class="login-left">
        <div class="brand">
          <h1 class="brand-title">OpsPilot</h1>
          <p class="brand-subtitle">Server monitoring & management made simple</p>
        </div>
        <div class="illustration">
          <svg viewBox="0 0 400 300" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Server illustration -->
            <rect x="80" y="60" width="240" height="40" rx="4" fill="#15181e" />
            <rect x="80" y="110" width="240" height="40" rx="4" fill="#15181e" />
            <rect x="80" y="160" width="240" height="40" rx="4" fill="#15181e" />
            <!-- Lights -->
            <circle cx="100" cy="80" r="4" fill="#14c6cb" />
            <circle cx="115" cy="80" r="4" fill="#7b42bc" />
            <circle cx="130" cy="80" r="4" fill="#1868f2" />
            <circle cx="100" cy="130" r="4" fill="#14c6cb" />
            <circle cx="115" cy="130" r="4" fill="#7b42bc" />
            <circle cx="130" cy="130" r="4" fill="#1868f2" />
            <circle cx="100" cy="180" r="4" fill="#14c6cb" />
            <circle cx="115" cy="180" r="4" fill="#7b42bc" />
            <circle cx="130" cy="180" r="4" fill="#1868f2" />
            <!-- Status indicator -->
            <path d="M280 80 L300 80 L300 180 L280 180 Z" fill="#14c6cb" opacity="0.2" />
            <path d="M285 90 L295 90 L295 170 L285 170 Z" fill="#14c6cb" />
          </svg>
        </div>
      </div>

      <!-- Right side - Login form -->
      <div class="login-form">
        <div class="form-header">
          <h2 class="form-title">Welcome back</h2>
          <p class="form-subtitle">Sign in to your account</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form-content"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="email">
            <el-input
              v-model="loginForm.email"
              placeholder="Email address"
              size="large"
              :prefix-icon="Message"
              :disabled="loading"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="Password"
              size="large"
              :prefix-icon="Lock"
              :disabled="loading"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <div class="form-actions">
            <el-checkbox v-model="rememberMe">Remember me</el-checkbox>
            <router-link to="/forgot-password" class="forgot-link"> Forgot password? </router-link>
          </div>

          <el-button type="primary" size="large" class="login-button" :loading="loading" @click="handleLogin">
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </el-button>

          <div class="form-footer setup-hint">
            <span class="footer-text">New installation?</span>
            <router-link to="/setup" class="register-link">One-time initial setup</router-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'

const router = useRouter()
const route = useRoute()
const authStore = useOpsPilotAuthStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  email: '',
  password: '',
})

const loginRules: FormRules = {
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Please enter your password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!loginFormRef.value) {
    return
  }

  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) {
      return
    }

    loading.value = true

    await authStore.login({
      email: loginForm.email,
      password: loginForm.password,
    })

    ElMessage.success('Login successful')

    // Redirect to dashboard or intended page
    const redirect = (route.query.redirect as string) || '/dashboard'
    await router.push(redirect)
  } catch (error: any) {
    console.error('Login error:', error)
    ElMessage.error(error.message || 'Login failed. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f2f3 0%, #d5d7db 100%);
  padding: 20px;

  .login-box {
    display: flex;
    width: 100%;
    max-width: 1000px;
    background: #ffffff;
    border-radius: 8px;
    box-shadow:
      rgba(97, 104, 117, 0.1) 0px 4px 12px,
      rgba(97, 104, 117, 0.05) 0px 2px 4px;
    overflow: hidden;
  }

  .login-left {
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

    .illustration {
      width: 100%;
      display: flex;
      justify-content: center;
      align-items: center;

      svg {
        width: 100%;
        max-width: 400px;
        height: auto;
      }
    }
  }

  .login-form {
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

    .login-form-content {
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

    .form-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;

      .forgot-link {
        font-size: 0.875rem;
        color: #2264d6;
        text-decoration: none;

        &:hover {
          color: #2b89ff;
          text-decoration: underline;
        }
      }
    }

    .login-button {
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
    }

    .form-footer {
      margin-top: 24px;
      text-align: center;

      .footer-text {
        font-size: 0.875rem;
        color: #656a76;
        margin-right: 8px;
      }

      .register-link {
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

html.dark .login-container {
  background: linear-gradient(135deg, #0d0e12 0%, #15181e 100%);

  .login-box {
    background: #15181e;
    border: 1px solid rgba(178, 182, 189, 0.4);
  }

  .login-form {
    .form-header {
      .form-title {
        color: #ffffff;
      }

      .form-subtitle {
        color: #d5d7db;
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
  .login-container .login-box {
    flex-direction: column;
    max-width: 500px;
  }

  .login-container .login-left {
    padding: 40px;
  }

  .login-container .login-form {
    padding: 40px;
  }
}
</style>

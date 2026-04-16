<template>
  <div class="error-page error-500">
    <div class="error-container">
      <div class="error-illustration">
        <svg viewBox="0 0 400 300" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Warning triangle -->
          <path d="M200 50 L350 250 L50 250 Z" fill="#bb5a00" stroke="#bb5a00" stroke-width="4" />
          <path d="M200 100 L300 220 L100 220 Z" fill="#ffffff" />
          <!-- Exclamation mark -->
          <rect x="193" y="120" width="14" height="60" rx="2" fill="#bb5a00" />
          <circle cx="200" cy="210" r="7" fill="#bb5a00" />
          <!-- 500 text -->
          <text
            x="200"
            y="280"
            text-anchor="middle"
            font-family="system-ui"
            font-size="40"
            font-weight="700"
            fill="#bb5a00"
          >
            Server Error
          </text>
        </svg>
      </div>
      <div class="error-content">
        <h1 class="error-title">Something went wrong</h1>
        <p class="error-description">
          We're experiencing technical difficulties. Please try again later or contact support if the problem persists.
        </p>
        <div class="error-actions">
          <el-button type="primary" size="large" @click="goHome"> Go to Dashboard </el-button>
          <el-button size="large" @click="goBack"> Go Back </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped lang="scss">
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f2f3;
  padding: 20px;
}

.error-container {
  text-align: center;
  max-width: 500px;
}

.error-illustration {
  margin-bottom: 32px;

  svg {
    width: 100%;
    max-width: 400px;
    height: auto;
  }
}

.error-content {
  .error-title {
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

  .error-description {
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      sans-serif;
    font-size: 1rem;
    font-weight: 400;
    color: #656a76;
    line-height: 1.6;
    margin: 0 0 32px 0;
  }
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

html.dark .error-page {
  background: #0d0e12;

  .error-content {
    .error-title {
      color: #ffffff;
    }

    .error-description {
      color: #d5d7db;
    }
  }
}
</style>

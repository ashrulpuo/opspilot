<template>
  <div class="error-page error-404">
    <div class="error-container">
      <div class="error-illustration">
        <svg viewBox="0 0 400 300" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Server rack -->
          <rect x="100" y="80" width="200" height="140" rx="4" fill="#15181e" />
          <rect x="110" y="90" width="180" height="30" rx="3" fill="#0d0e12" />
          <rect x="110" y="130" width="180" height="30" rx="3" fill="#0d0e12" />
          <rect x="110" y="170" width="180" height="30" rx="3" fill="#0d0e12" />
          <!-- Status lights -->
          <circle cx="130" cy="105" r="5" fill="#14c6cb" />
          <circle cx="145" cy="105" r="5" fill="#14c6cb" />
          <circle cx="160" cy="105" r="5" fill="#14c6cb" />
          <circle cx="130" cy="145" r="5" fill="#656a76" />
          <circle cx="145" cy="145" r="5" fill="#656a76" />
          <circle cx="160" cy="145" r="5" fill="#656a76" />
          <circle cx="130" cy="185" r="5" fill="#656a76" />
          <circle cx="145" cy="185" r="5" fill="#656a76" />
          <circle cx="160" cy="185" r="5" fill="#656a76" />
          <!-- 404 text -->
          <text
            x="200"
            y="250"
            text-anchor="middle"
            font-family="system-ui"
            font-size="60"
            font-weight="700"
            fill="#731e25"
          >
            404
          </text>
        </svg>
      </div>
      <div class="error-content">
        <h1 class="error-title">Page not found</h1>
        <p class="error-description">The page you're looking for doesn't exist or has been moved.</p>
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

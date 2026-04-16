<template>
  <div class="dashboard-container">
    <!-- Page Header -->
    <div class="page-header">
      <h1 class="page-title">Dashboard</h1>
      <p class="page-subtitle">Welcome back, {{ authStore.user?.full_name || authStore.user?.email }}</p>
    </div>

    <!-- Stats Cards -->
    <div v-if="dashboardStore.stats" class="stats-grid">
      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-primary">
          <el-icon><Monitor /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Total Servers</p>
          <p class="stat-value">{{ dashboardStore.stats.servers_total }}</p>
          <p class="stat-change stat-change-positive">
            <el-icon><CaretTop /></el-icon>
            {{ dashboardStore.stats.servers_online }} online
          </p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-accent">
          <el-icon><OfficeBuilding /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Organizations</p>
          <p class="stat-value">{{ dashboardStore.stats.organizations_total }}</p>
          <p class="stat-change">Active workspace</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-warning">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Active Alerts</p>
          <p class="stat-value">{{ dashboardStore.stats.alerts_active }}</p>
          <p v-if="dashboardStore.stats.alerts_critical > 0" class="stat-change stat-change-critical">
            <el-icon><CaretTop /></el-icon>
            {{ dashboardStore.stats.alerts_critical }} critical
          </p>
          <p v-else class="stat-change">All systems normal</p>
        </div>
      </div>

      <div class="stat-card hc-card">
        <div class="stat-icon stat-icon-success">
          <el-icon><Operation /></el-icon>
        </div>
        <div class="stat-content">
          <p class="stat-label">Commands Today</p>
          <p class="stat-value">{{ dashboardStore.stats.commands_today }}</p>
          <p class="stat-change">Last 24 hours</p>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Server Health -->
      <div class="section-card hc-card">
        <div class="section-header">
          <h2 class="section-title">Server Health</h2>
          <el-button link type="primary" @click="$router.push('/servers')">View all</el-button>
        </div>
        <div class="server-health-list">
          <div
            v-for="server in dashboardStore.serverHealth.slice(0, 5)"
            :key="server.server_id"
            class="server-health-item"
          >
            <div class="server-info">
              <div class="server-status" :class="`status-${server.status}`">
                <span class="status-dot"></span>
              </div>
              <div class="server-details">
                <p class="server-name">{{ server.server_name }}</p>
                <p class="server-metrics">
                  CPU: {{ server.cpu_usage.toFixed(1) }}% | RAM: {{ server.memory_usage.toFixed(1) }}% | Disk:
                  {{ server.disk_usage.toFixed(1) }}%
                </p>
              </div>
            </div>
            <el-progress
              :percentage="Math.max(server.cpu_usage, server.memory_usage)"
              :color="getHealthColor(server)"
              :show-text="false"
              :stroke-width="4"
              class="server-progress"
            />
          </div>
          <el-empty v-if="dashboardStore.serverHealth.length === 0" description="No servers connected" />
        </div>
      </div>

      <!-- Recent Alerts -->
      <div class="section-card hc-card">
        <div class="section-header">
          <h2 class="section-title">Recent Alerts</h2>
          <el-button link type="primary" @click="$router.push('/alerts')">View all</el-button>
        </div>
        <div class="alerts-list">
          <div v-for="alert in dashboardStore.recentAlerts.slice(0, 5)" :key="alert.id" class="alert-item">
            <div class="alert-icon" :class="`alert-${alert.severity}`">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="alert-content">
              <p class="alert-title">{{ alert.title }}</p>
              <p class="alert-message">{{ alert.message }}</p>
              <p class="alert-server">{{ alert.server_name }}</p>
            </div>
            <div class="alert-time">
              <p class="time-text">{{ formatTime(alert.created_at) }}</p>
            </div>
          </div>
          <el-empty v-if="dashboardStore.recentAlerts.length === 0" description="No recent alerts" />
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions-section hc-card">
      <h2 class="section-title">Quick Actions</h2>
      <div class="quick-actions-grid">
        <el-button type="default" class="quick-action-btn" @click="$router.push('/servers')">
          <el-icon><Plus /></el-icon>
          Add Server
        </el-button>
        <el-button type="default" class="quick-action-btn" @click="$router.push('/organizations')">
          <el-icon><OfficeBuilding /></el-icon>
          Create Organization
        </el-button>
        <el-button type="default" class="quick-action-btn" @click="$router.push('/alerts')">
          <el-icon><View /></el-icon>
          View Alerts
        </el-button>
        <el-button type="default" class="quick-action-btn" @click="$router.push('/settings')">
          <el-icon><Setting /></el-icon>
          Settings
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot'
import { useOpsPilotDashboardStore } from '@/stores/modules/opspilot'
import {
  Monitor,
  OfficeBuilding,
  Warning,
  Operation,
  Bell,
  Plus,
  View,
  Setting,
  CaretTop,
} from '@element-plus/icons-vue'

const authStore = useOpsPilotAuthStore()
const dashboardStore = useOpsPilotDashboardStore()

const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) {
    return 'Just now'
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }
  return `${diffDays}d ago`
}

const getHealthColor = (server: any) => {
  const maxUsage = Math.max(server.cpu_usage, server.memory_usage, server.disk_usage)
  if (server.status !== 'online') {
    return '#656a76'
  }
  if (maxUsage > 90) {
    return '#731e25'
  }
  if (maxUsage > 75) {
    return '#bb5a00'
  }
  return '#14c6cb'
}

onMounted(async () => {
  await dashboardStore.fetchDashboard()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;

  .page-title {
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

  .page-subtitle {
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

html.dark .page-header {
  .page-title {
    color: #ffffff;
  }

  .page-subtitle {
    color: #d5d7db;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;

    &.stat-icon-primary {
      background: rgba(21, 24, 30, 0.1);
      color: #15181e;
    }

    &.stat-icon-accent {
      background: rgba(33, 150, 243, 0.1);
      color: #2196f3;
    }

    &.stat-icon-warning {
      background: rgba(255, 152, 0, 0.1);
      color: #ff9800;
    }

    &.stat-icon-success {
      background: rgba(20, 198, 203, 0.1);
      color: #14c6cb;
    }
  }

  .stat-content {
    flex: 1;

    .stat-label {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.875rem;
      font-weight: 500;
      color: #656a76;
      line-height: 1.4;
      margin: 0 0 4px 0;
    }

    .stat-value {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1.75rem;
      font-weight: 700;
      color: #000000;
      line-height: 1.2;
      margin: 0 0 4px 0;
    }

    .stat-change {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.8125rem;
      font-weight: 500;
      color: #14c6cb;
      line-height: 1.4;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 4px;

      &.stat-change-critical {
        color: #731e25;
      }

      &.stat-change-positive {
        color: #14c6cb;
      }
    }
  }
}

html.dark .stat-card {
  .stat-icon {
    &.stat-icon-primary {
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
    }
  }

  .stat-content {
    .stat-label {
      color: #b2b6bd;
    }

    .stat-value {
      color: #ffffff;
    }
  }
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.section-card {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    .section-title {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 1.25rem;
      font-weight: 600;
      color: #000000;
      line-height: 1.3;
      margin: 0;
    }
  }
}

html.dark .section-card .section-header .section-title {
  color: #ffffff;
}

.server-health-list,
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.server-health-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f1f2f3;
  border-radius: 8px;

  .server-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;

    .server-status {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;

      &.status-online {
        background: #14c6cb;
      }

      &.status-offline {
        background: #656a76;
      }

      &.status-error {
        background: #731e25;
      }

      &.status-connecting {
        background: #bb5a00;
        animation: pulse 1.5s ease-in-out infinite;
      }
    }

    .server-details {
      flex: 1;

      .server-name {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 0.9375rem;
        font-weight: 600;
        color: #000000;
        line-height: 1.4;
        margin: 0 0 4px 0;
      }

      .server-metrics {
        font-family:
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          'Segoe UI',
          sans-serif;
        font-size: 0.8125rem;
        font-weight: 400;
        color: #656a76;
        line-height: 1.4;
        margin: 0;
      }
    }
  }

  .server-progress {
    width: 120px;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

html.dark .server-health-item {
  background: #0d0e12;

  .server-info .server-details {
    .server-name {
      color: #ffffff;
    }

    .server-metrics {
      color: #b2b6bd;
    }
  }
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #f1f2f3;
  border-radius: 8px;

  .alert-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;

    &.alert-critical {
      background: rgba(115, 30, 37, 0.1);
      color: #731e25;
    }

    &.alert-warning {
      background: rgba(187, 90, 0, 0.1);
      color: #bb5a00;
    }

    &.alert-info {
      background: rgba(33, 150, 243, 0.1);
      color: #2196f3;
    }
  }

  .alert-content {
    flex: 1;

    .alert-title {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.9375rem;
      font-weight: 600;
      color: #000000;
      line-height: 1.4;
      margin: 0 0 4px 0;
    }

    .alert-message {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.875rem;
      font-weight: 400;
      color: #656a76;
      line-height: 1.4;
      margin: 0 0 4px 0;
    }

    .alert-server {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.8125rem;
      font-weight: 500;
      color: #b2b6bd;
      line-height: 1.4;
      margin: 0;
    }
  }

  .alert-time {
    .time-text {
      font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif;
      font-size: 0.75rem;
      font-weight: 500;
      color: #656a76;
      line-height: 1.4;
      margin: 0;
      white-space: nowrap;
    }
  }
}

html.dark .alert-item {
  background: #0d0e12;

  .alert-content {
    .alert-title {
      color: #ffffff;
    }

    .alert-message {
      color: #b2b6bd;
    }

    .alert-server {
      color: #656a76;
    }
  }

  .alert-time .time-text {
    color: #b2b6bd;
  }
}

.quick-actions-section {
  padding: 24px;

  .section-title {
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      sans-serif;
    font-size: 1.125rem;
    font-weight: 600;
    color: #000000;
    line-height: 1.3;
    margin: 0 0 20px 0;
  }
}

html.dark .quick-actions-section .section-title {
  color: #ffffff;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.quick-action-btn {
  height: 48px;
  border-radius: 5px;
  font-weight: 500;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #d5d7db;
  color: #3b3d45;

  &:hover {
    background: #f1f2f3;
    border-color: #b2b6bd;
  }
}

html.dark .quick-action-btn {
  background: #0d0e12;
  border-color: rgba(178, 182, 189, 0.4);
  color: #d5d7db;

  &:hover {
    background: #15181e;
    border-color: rgba(178, 182, 189, 0.4);
  }
}

// Responsive design
@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .page-header .page-title {
    font-size: 1.5rem;
  }

  .quick-actions-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

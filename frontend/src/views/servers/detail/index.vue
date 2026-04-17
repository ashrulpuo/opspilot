<template>
  <div class="server-detail">
    <!-- Server Detail Header -->
    <ServerDetailHeader :server-id="serverId" />
    
    <!-- Tabs Navigation -->
    <el-tabs v-model="activeTab" class="server-detail-tabs">
      <!-- Overview Tab -->
      <el-tab-pane label="Overview" name="overview">
        <ServerOverview :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Metrics Tab (Real-Time) -->
      <el-tab-pane label="Metrics" name="metrics">
        <ServerMetrics :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Salt Info Tab -->
      <el-tab-pane label="Salt Info" name="salt">
        <SaltInfo :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Services Tab (Real-Time) -->
      <el-tab-pane label="Services" name="services">
        <SaltServices :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Processes Tab (Real-Time) -->
      <el-tab-pane label="Processes" name="processes">
        <SaltProcesses :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Packages Tab -->
      <el-tab-pane label="Packages" name="packages">
        <SaltPackages :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Logs Tab (Real-Time) -->
      <el-tab-pane label="Logs" name="logs">
        <SaltLogs :server-id="serverId" />
      </el-tab-pane>
      
      <!-- Alerts Tab (Real-Time) -->
      <el-tab-pane label="Alerts" name="alerts">
        <SaltAlerts :server-id="serverId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSaltStream } from '@/composables/useSaltStream'

// Import components
import ServerDetailHeader from './components/ServerDetailHeader.vue'
import ServerOverview from './components/ServerOverview.vue'
import ServerMetrics from './components/SaltMetrics.vue'
import SaltInfo from './components/SaltInfo.vue'
import SaltServices from './components/SaltServices.vue'
import SaltProcesses from './components/SaltProcesses.vue'
import SaltPackages from './components/SaltPackages.vue'
import SaltLogs from './components/SaltLogs.vue'
import SaltAlerts from './components/SaltAlerts.vue'

const route = useRoute()
const serverId = route.params.id as string
const activeTab = ref('overview')

// Use SSE composable
const {
  metrics,
  alerts,
  serviceStates,
  isConnected,
  disconnectAll
} = useSaltStream(serverId)

// Set default tab on mount
onMounted(() => {
  console.log('Server detail page mounted for server:', serverId)
  console.log('SSE connected:', isConnected.value)
  
  // Set default tab based on route query
  if (route.query.tab) {
    activeTab.value = route.query.tab as string
  }
})

// Cleanup on unmount
onUnmounted(() => {
  console.log('Server detail page unmounted for server:', serverId)
  disconnectAll()
})

// Helper functions for displaying metrics
const formatMetricValue = (value: number | undefined, unit: string) => {
  if (value === undefined || value === null) return '-'
  return `${value} ${unit}`
}

const getMetricColor = (value: number | undefined) => {
  if (value === undefined) return '#909399'
  if (value < 50) return '#67C23A'  // Green
  if (value < 70) return '#E6A23C'  // Yellow
  if (value < 85) return '#F59E0B'  // Orange
  return '#F56C6C'  // Red
}

// Expose to template
defineExpose({
  activeTab,
  metrics,
  alerts,
  serviceStates,
  isConnected,
  formatMetricValue,
  getMetricColor
})
</script>

<style scoped>
.server-detail {
  padding: 20px;
  min-height: calc(100vh - 60px);
}

.server-detail-tabs {
  margin-top: 20px;
}

.server-detail-tabs :deep(.el-tabs__header) {
  font-size: 14px;
  font-weight: 500;
}

.server-detail-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  padding: 0 20px;
}

.server-detail-tabs :deep(.el-tab-pane) {
  padding: 0;
}
</style>

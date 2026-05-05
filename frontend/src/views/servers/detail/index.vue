<template>
  <div class="server-detail">
    <ServerDetailHeader :server-id="serverId" />

    <el-tabs v-model="activeTab" class="server-detail-tabs">
      <el-tab-pane name="overview">
        <template #label>
          <span class="tab-label"><el-icon><Monitor /></el-icon>Overview</span>
        </template>
        <ServerOverview
          v-if="visitedTabs.has('overview')"
          v-show="activeTab === 'overview'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="metrics">
        <template #label>
          <span class="tab-label"><el-icon><TrendCharts /></el-icon>Metrics</span>
        </template>
        <ServerMetrics
          v-if="visitedTabs.has('metrics')"
          v-show="activeTab === 'metrics'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="salt">
        <template #label>
          <span class="tab-label"><el-icon><Setting /></el-icon>Salt Info</span>
        </template>
        <SaltInfo
          v-if="visitedTabs.has('salt')"
          v-show="activeTab === 'salt'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="services">
        <template #label>
          <span class="tab-label"><el-icon><Tools /></el-icon>Services</span>
        </template>
        <SaltServices
          v-if="visitedTabs.has('services')"
          v-show="activeTab === 'services'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="processes">
        <template #label>
          <span class="tab-label"><el-icon><List /></el-icon>Processes</span>
        </template>
        <SaltProcesses
          v-if="visitedTabs.has('processes')"
          v-show="activeTab === 'processes'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="packages">
        <template #label>
          <span class="tab-label">
            <el-icon><Box /></el-icon>Packages
            <el-badge
              v-if="packageUpdateCount > 0"
              :value="packageUpdateCount"
              class="tab-badge"
            />
          </span>
        </template>
        <SaltPackages
          v-if="visitedTabs.has('packages')"
          v-show="activeTab === 'packages'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="logs">
        <template #label>
          <span class="tab-label"><el-icon><Document /></el-icon>Logs</span>
        </template>
        <SaltLogs
          v-if="visitedTabs.has('logs')"
          v-show="activeTab === 'logs'"
          :server-id="serverId"
        />
      </el-tab-pane>

      <el-tab-pane name="alerts">
        <template #label>
          <span class="tab-label">
            <el-icon><Bell /></el-icon>Live Alerts
            <el-badge
              v-if="unreadAlertCount > 0"
              :value="unreadAlertCount"
              type="danger"
              class="tab-badge"
            />
          </span>
        </template>
        <SaltAlerts
          v-if="visitedTabs.has('alerts')"
          v-show="activeTab === 'alerts'"
          :server-id="serverId"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, TrendCharts, Setting, Tools, List, Box, Document, Bell } from '@element-plus/icons-vue'
import { useSaltStream } from '@/composables/useSaltStream'

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
const router = useRouter()
const serverId = route.params.id as string

const VALID_TABS = ['overview', 'metrics', 'salt', 'services', 'processes', 'packages', 'logs', 'alerts']
const initialTab = VALID_TABS.includes(route.query.tab as string) ? (route.query.tab as string) : 'overview'
const activeTab = ref(initialTab)

// Lazy mount: tab component only mounts on first visit, then stays alive (v-show)
const visitedTabs = reactive(new Set<string>([initialTab]))

watch(activeTab, (tab) => {
  visitedTabs.add(tab)
  router.replace({ query: { ...route.query, tab } })
})

const { unreadAlerts, packageUpdateCount } = useSaltStream(serverId)

const unreadAlertCount = computed(() => {
  const val = unreadAlerts.value
  if (!val) return 0
  return Array.isArray(val) ? val.length : (typeof val === 'number' ? val : 0)
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
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--el-bg-color);
  margin-bottom: 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

.server-detail-tabs :deep(.el-tabs__content) {
  padding-top: 20px;
}

.server-detail-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  font-weight: 500;
  padding: 0 18px;
  height: 44px;
  line-height: 44px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  position: relative;
}

.tab-badge {
  margin-left: 4px;
}

.tab-badge :deep(.el-badge__content) {
  transform: none;
  position: relative;
  top: auto;
  right: auto;
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 4px;
  min-width: 16px;
}
</style>

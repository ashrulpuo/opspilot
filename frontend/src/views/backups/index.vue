<template>
  <div class="backups-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Backups</h1>
        <p class="page-subtitle">Automate and manage your server backups</p>
      </div>
      <el-button type="primary" @click="showScheduleDialog = true">
        <el-icon><Clock /></el-icon>
        Schedule Backup
      </el-button>
    </div>

    <!-- Organization Selector -->
    <div class="org-selector" v-if="orgStore.organizations.length > 1">
      <el-select v-model="selectedOrgId" placeholder="Select organization" @change="handleOrgChange">
        <el-option v-for="org in orgStore.organizations" :key="org.id" :label="org.name" :value="org.id" />
      </el-select>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="backup-tabs">
      <!-- Schedules Tab -->
      <el-tab-pane label="Schedules" name="schedules">
        <div class="schedules-content">
          <el-empty description="Backup schedules coming soon. Salt runner integration is required." />
        </div>
      </el-tab-pane>

      <!-- History Tab -->
      <el-tab-pane label="History" name="history">
        <div class="history-content">
          <el-empty description="Backup history coming soon. Salt runner integration is required." />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Quick Actions -->
    <div class="quick-actions-section hc-card">
      <h2 class="section-title">Quick Actions</h2>
      <div class="quick-actions-grid">
        <el-button type="default" class="quick-action-btn" @click="handleRunBackup">
          <el-icon><VideoPlay /></el-icon>
          Run Ad-Hoc Backup
        </el-button>
        <el-button type="default" class="quick-action-btn" @click="showScheduleDialog = true">
          <el-icon><Clock /></el-icon>
          Schedule Backup
        </el-button>
        <el-button type="default" class="quick-action-btn" @click="goToSaltDocs">
          <el-icon><Document /></el-icon>
          Salt Documentation
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock, VideoPlay, Document } from '@element-plus/icons-vue'
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot'
import { useOpsPilotServerStore } from '@/stores/modules/opspilot'

const router = useRouter()
const orgStore = useOpsPilotOrganizationStore()
const serverStore = useOpsPilotServerStore()

const showScheduleDialog = ref(false)
const activeTab = ref('schedules')
const selectedOrgId = ref<string>()

const handleOrgChange = async (orgId: string) => {
  await serverStore.fetchServers(orgId)
}

const handleRunBackup = () => {
  ElMessage.info('Ad-hoc backup functionality requires Salt runner integration. Coming soon in Phase 9+.')
}

const goToSaltDocs = () => {
  window.open('https://docs.saltproject.com/en/latest/', '_blank')
}

onMounted(async () => {
  // Fetch organizations
  if (orgStore.organizations.length === 0) {
    await orgStore.fetchOrganizations()
  }

  // Set selected organization
  selectedOrgId.value = orgStore.currentOrganization?.id

  // Fetch servers
  await serverStore.fetchServers(selectedOrgId.value)
})
</script>

<style scoped lang="scss">
.backups-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
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
}

html.dark .page-header .header-left {
  .page-title {
    color: #ffffff;
  }

  .page-subtitle {
    color: #d5d7db;
  }
}

.org-selector {
  margin-bottom: 24px;
  max-width: 400px;
}

.backup-tabs {
  margin-bottom: 24px;

  .schedules-content,
  .history-content {
    padding: 40px 24px;
    text-align: center;
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
@media (max-width: 768px) {
  .backups-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .header-left .page-title {
      font-size: 1.5rem;
    }
  }

  .quick-actions-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

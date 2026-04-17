<template>
  <div class="server-detail-header">
    <el-page-header @back="goBack">
      <template #content>
        <div class="header-content">
          <h1 class="server-name">{{ server.name }}</h1>
          <div class="server-meta">
            <el-tag type="info" size="small">{{ server.hostname }}</el-tag>
            <el-tag type="success" size="small" v-if="server.is_online">Online</el-tag>
            <el-tag type="danger" size="small" v-else>Offline</el-tag>
          </div>
        </div>
      </template>
      <template #extra>
        <div class="header-actions">
          <el-button type="primary" size="small" :icon="Connection" @click="testConnection">
            Test Connection
          </el-button>
          <el-button type="danger" size="small" :icon="Delete" @click="deleteServer">
            Delete Server
          </el-button>
        </div>
      </template>
    </el-page-header>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Delete } from '@element-plus/icons-vue'

import { useServerStore } from '@/stores/server'

const props = defineProps<{
  serverId: string
}>()

const router = useRouter()
const serverStore = useServerStore()

const server = computed(() => serverStore.servers[props.serverId] || {})

const goBack = () => {
  router.push({ name: 'servers' })
}

const testConnection = async () => {
  ElMessage({
    message: 'Testing connection...',
    type: 'info',
    duration: 2000
  })
}

const deleteServer = async () => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete server "${server.value.name}"? This action cannot be undone.`,
      'Delete Server',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'danger'
      }
    )
    
    await serverStore.deleteServer(props.serverId)
    
    ElMessage({
      message: 'Server deleted successfully',
      type: 'success',
      duration: 3000
    })
    
    router.push({ name: 'servers' })
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete server:', error)
      ElMessage.error('Failed to delete server')
    }
  }
}
</script>

<style scoped>
.server-detail-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.server-name {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.server-meta {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>

<template>
  <div>
    <el-empty v-if="!loading && !items.length" description="No credentials yet" :image-size="64" />
    <el-table v-else v-loading="loading" :data="items" stripe class="asset-table">
      <el-table-column label="Name" prop="name" min-width="160">
        <template #default="{ row }"><span class="asset-name">{{ row.name }}</span></template>
      </el-table-column>
      <el-table-column label="Type" width="120">
        <template #default="{ row }"><el-tag size="small" type="info">{{ row.credential_type }}</el-tag></template>
      </el-table-column>
      <el-table-column label="Username" prop="username" width="150" show-overflow-tooltip />
      <el-table-column label="URL" prop="url" min-width="160" show-overflow-tooltip />
      <el-table-column label="Env" width="90">
        <template #default="{ row }">
          <el-tag :type="envType(row.environment)" size="small">{{ row.environment }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Secret" width="110" align="center">
        <template #default="{ row }">
          <el-button v-if="row.has_secret" size="small" link @click="reveal(row.id)">
            <el-icon><View /></el-icon>&nbsp;Reveal
          </el-button>
          <span v-else class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column width="100" align="right">
        <template #default="{ row }">
          <el-button size="small" link @click="$emit('edit', row)">Edit</el-button>
          <el-button size="small" link type="danger" @click="$emit('delete', row.id)">Del</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="revealVisible" title="Credential Secret" width="420px" :close-on-click-modal="false">
      <div class="reveal-box">
        <code class="reveal-value">{{ revealedValue }}</code>
        <el-button size="small" :icon="CopyDocument" circle @click="copyValue" />
      </div>
      <p class="reveal-note">Auto-hidden in {{ countdownSecs }}s</p>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { View, CopyDocument } from '@element-plus/icons-vue'
import type { Credential } from '@/api/opspilot/registry'
import { RegistryAPI } from '@/api/opspilot/registry'

defineProps<{ items: Credential[]; loading: boolean }>()
defineEmits<{ edit: [item: Credential]; delete: [id: string] }>()

const revealVisible = ref(false)
const revealedValue = ref('')
const countdownSecs = ref(30)
let timer: ReturnType<typeof setInterval> | null = null

async function reveal(id: string) {
  const res = await RegistryAPI.revealCredentialSecret(id)
  revealedValue.value = res.value
  revealVisible.value = true
  countdownSecs.value = 30
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    countdownSecs.value--
    if (countdownSecs.value <= 0) {
      revealVisible.value = false
      revealedValue.value = ''
      clearInterval(timer!)
    }
  }, 1000)
}

async function copyValue() {
  await navigator.clipboard.writeText(revealedValue.value)
  ElMessage.success('Copied')
}

function envType(env: string) {
  return env === 'prod' ? 'danger' : env === 'staging' ? 'warning' : 'info'
}
</script>

<style scoped>
.asset-name { font-weight: 600; }
.asset-table { border-radius: 8px; }
.text-muted { color: var(--el-text-color-placeholder); font-size: 12px; }
.reveal-box { display: flex; align-items: center; gap: 12px; background: var(--el-fill-color-light); padding: 12px 16px; border-radius: 8px; }
.reveal-value { font-size: 14px; flex: 1; word-break: break-all; }
.reveal-note { font-size: 12px; color: var(--el-text-color-secondary); margin: 8px 0 0; }
</style>

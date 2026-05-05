<template>
  <div>
    <el-empty v-if="!loading && !items.length" description="No audit entries yet" :image-size="64" />
    <el-table v-else v-loading="loading" :data="items" stripe>
      <el-table-column label="Time" width="170">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="Action" width="100">
        <template #default="{ row }">
          <el-tag :type="actionType(row.action)" size="small">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Asset Type" prop="asset_type" width="120" />
      <el-table-column label="Asset ID" prop="asset_id" min-width="200" show-overflow-tooltip />
      <el-table-column label="IP" prop="ip_address" width="130" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import type { AuditLog } from '@/api/opspilot/registry'

defineProps<{ items: AuditLog[]; loading: boolean }>()

function fmtDate(d: string) {
  return new Date(d).toLocaleString()
}

function actionType(action: string) {
  if (action === 'reveal') return 'warning'
  if (action === 'delete') return 'danger'
  if (action === 'create') return 'success'
  return 'info'
}
</script>

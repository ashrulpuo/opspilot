<template>
  <div>
    <el-empty v-if="!loading && !items.length" description="No SSL certs yet" :image-size="64" />
    <el-table v-else v-loading="loading" :data="items" stripe class="asset-table">
      <el-table-column label="Domain" prop="domain_name" min-width="180">
        <template #default="{ row }"><span class="asset-name">{{ row.domain_name }}</span></template>
      </el-table-column>
      <el-table-column label="Issuer" prop="issuer" width="160" show-overflow-tooltip />
      <el-table-column label="Provider" prop="provider" width="130" />
      <el-table-column label="Expires" width="130">
        <template #default="{ row }"><ExpiryBadge :date="row.expires_at" /></template>
      </el-table-column>
      <el-table-column label="Auto-renew" width="110">
        <template #default="{ row }">
          <el-tag :type="row.auto_renew ? 'success' : 'info'" size="small">{{ row.auto_renew ? 'Yes' : 'No' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column width="100" align="right">
        <template #default="{ row }">
          <el-button size="small" link @click="$emit('edit', row)">Edit</el-button>
          <el-button size="small" link type="danger" @click="$emit('delete', row.id)">Del</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import type { SslCert } from '@/api/opspilot/registry'
import ExpiryBadge from './ExpiryBadge.vue'
defineProps<{ items: SslCert[]; loading: boolean }>()
defineEmits<{ edit: [item: SslCert]; delete: [id: string] }>()
</script>

<style scoped>
.asset-name { font-weight: 600; }
.asset-table { border-radius: 8px; }
</style>

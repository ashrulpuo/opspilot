<template>
  <span v-if="!date" class="text-muted">—</span>
  <el-tag v-else :type="tagType" size="small">{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ date?: string | null }>()
const daysLeft = computed(() => {
  if (!props.date) return null
  return Math.ceil((new Date(props.date).getTime() - Date.now()) / 86400000)
})
const tagType = computed(() => {
  const d = daysLeft.value
  if (d === null) return 'info'
  if (d < 0 || d <= 14) return 'danger'
  if (d <= 30) return 'warning'
  return 'success'
})
const label = computed(() => {
  const d = daysLeft.value
  if (d === null) return '—'
  if (d < 0) return `Expired ${Math.abs(d)}d ago`
  if (d === 0) return 'Expires today'
  return `${d}d left`
})
</script>

<style scoped>
.text-muted { color: var(--el-text-color-placeholder); }
</style>

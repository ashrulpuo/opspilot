<template>
  <div class="salt-metrics-placeholder">
    <el-card shadow="never">
      <el-empty description="Salt Metrics component will be rendered here" :image-size="150">
        <el-icon :size="50" color="#909399"><TrendCharts /></el-icon>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { TrendCharts } from '@element-plus/icons-vue'

defineProps<{
  serverId: string
}>()
</script>

<style scoped>
.salt-metrics-placeholder {
  padding: 20px;
}
</style>

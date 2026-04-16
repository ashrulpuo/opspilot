<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">Organization Detail</h1>
    </div>
    <div class="hc-card">
      <el-empty description="Organization detail view coming soon" />
    </div>
  </div>
</template>

<script setup lang="ts">
// Organization detail view - coming soon
</script>

<style scoped lang="scss">
.page-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

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
    margin: 0;
  }
}

html.dark .page-header .page-title {
  color: #ffffff;
}
</style>

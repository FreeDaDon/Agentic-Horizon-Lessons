<script setup lang="ts">
defineProps<{
  html: string
}>()
</script>

<template>
  <div class="preview-container">
    <div class="preview-header">
      <span class="preview-title">Preview</span>
    </div>
    <div class="preview-content prose" v-html="html"></div>
  </div>
</template>

<style scoped>
.preview-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-primary);
}

.preview-header {
  padding: 0.75rem 1rem;
  background-color: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.preview-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>

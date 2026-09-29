<script setup lang="ts">
/**
 * Interactive File Tree Demo Application
 * Showcases the FileTreeView component with sample data
 */
import FileTreeView from './components/FileTreeView.vue';
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>Interactive File Tree</h1>
      <p>A drag-and-drop enabled file browser component built with Vue 3 + TypeScript</p>
    </header>
    <main class="app-main">
      <FileTreeView />
    </main>
    <footer class="app-footer">
      <p>
        <strong>Features:</strong>
        Click to select | Double-click to expand folders | Drag and drop to reorganize |
        Use toolbar buttons to create files/folders
      </p>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  gap: 20px;
}

.app-header {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.app-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
}

.app-header p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.app-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.app-main > :deep(.file-tree-view) {
  flex: 1;
  min-height: 400px;
}

.app-footer {
  text-align: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  color: #6b7280;
  font-size: 13px;
}

.app-footer p {
  margin: 0;
}

.app-footer strong {
  color: #374151;
}
</style>

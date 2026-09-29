<script setup lang="ts">
import { onMounted, onBeforeUnmount, computed, watch, ref } from 'vue';
import { useFileTreeStore } from '../stores/fileTreeStore';
import FileTreeNode from './FileTreeNode.vue';
import type { FileTreeNode as FileTreeNodeType, FileTreeViewOptions } from '../types/fileTree';
import sampleFileTree from '../data/sampleFileTree.json';
import {
  FilePlus,
  FolderPlus,
  Download,
  Trash2,
  RefreshCw,
  Search,
  X,
} from 'lucide-vue-next';

interface Props {
  initialData?: FileTreeNodeType[];
  options?: FileTreeViewOptions;
}

const props = withDefaults(defineProps<Props>(), {
  options: () => ({
    readOnly: false,
    showToolbar: true,
    showDescription: true,
    compactMode: false,
    maxDepth: 20,
    allowDragDrop: true,
  }),
});

const store = useFileTreeStore();

const showEmptyState = computed(() => store.tree.length === 0);
const selectedNode = computed(() => store.selectedNode);
const selectedNodePath = computed(() =>
  store.selectedNodeId ? store.getNodePath(store.selectedNodeId) : ''
);

// Search functionality
const searchInputRef = ref<HTMLInputElement | null>(null);
let searchDebounceTimer: number | null = null;

const handleSearchInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const query = target.value;

  // Clear existing timer
  if (searchDebounceTimer !== null) {
    clearTimeout(searchDebounceTimer);
  }

  // Set new debounced search
  searchDebounceTimer = setTimeout(() => {
    store.setSearchQuery(query);
  }, 300) as unknown as number;
};

const handleClearSearch = () => {
  store.clearSearch();
  if (searchInputRef.value) {
    searchInputRef.value.value = '';
  }
};

const noSearchResults = computed(() =>
  store.isSearchActive && store.filteredNodeIds !== null && store.filteredNodeIds.size === 0
);

// Watch for external data changes
watch(() => props.initialData, (newData) => {
  if (newData) {
    store.loadTree(newData);
  }
}, { deep: true });

const handleNewFile = () => {
  const name = prompt('Enter file name:');
  if (name && name.trim()) {
    const parentId = store.selectedNodeId;
    const selectedNode = store.selectedNode;

    // If selected node is a file, add to its parent
    let targetParentId = parentId;
    if (selectedNode && selectedNode.type === 'file') {
      targetParentId = null; // Will add to root if parent not found
      // TODO: Find actual parent of file
    }

    store.addNewFile(targetParentId, name.trim());
  }
};

const handleNewFolder = () => {
  const name = prompt('Enter folder name:');
  if (name && name.trim()) {
    const parentId = store.selectedNodeId;
    const selectedNode = store.selectedNode;

    // If selected node is a file, add to its parent
    let targetParentId = parentId;
    if (selectedNode && selectedNode.type === 'file') {
      targetParentId = null; // Will add to root if parent not found
      // TODO: Find actual parent of file
    }

    store.addNewFolder(targetParentId, name.trim());
  }
};

const handleDelete = () => {
  if (store.selectedNodeId) {
    const node = store.selectedNode;
    if (node && confirm(`Are you sure you want to delete "${node.name}"?`)) {
      store.deleteNode(store.selectedNodeId);
    }
  }
};

const handleExport = () => {
  const jsonData = store.exportTree();
  const blob = new Blob([jsonData], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'file-tree.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const handleRefresh = () => {
  if (props.initialData) {
    store.loadTree(props.initialData);
  }
};

const handleKeyDown = (event: KeyboardEvent) => {
  // Handle Delete key
  if (event.key === 'Delete' && store.selectedNodeId) {
    handleDelete();
  }

  // Handle Cmd/Ctrl + F to focus search
  if ((event.metaKey || event.ctrlKey) && event.key === 'f') {
    event.preventDefault();
    if (searchInputRef.value) {
      searchInputRef.value.focus();
    }
  }

  // Handle ESC to clear search
  if (event.key === 'Escape') {
    if (store.searchQuery.length > 0) {
      event.preventDefault();
      handleClearSearch();
      if (searchInputRef.value) {
        searchInputRef.value.blur();
      }
    }
  }
};

onMounted(() => {
  // Load tree data
  if (props.initialData) {
    store.loadTree(props.initialData);
  } else {
    // Load sample data if no initial data provided
    store.loadTree(sampleFileTree as FileTreeNodeType[]);
  }

  // Add keyboard event listener
  window.addEventListener('keydown', handleKeyDown);
});

// Clean up event listener
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<template>
  <div class="file-tree-view" :class="{ 'compact-mode': options?.compactMode }">
    <!-- Toolbar -->
    <div v-if="options?.showToolbar" class="file-tree-toolbar">
      <div class="toolbar-left">
        <button
          v-if="!options?.readOnly"
          class="toolbar-button"
          title="New File"
          @click="handleNewFile"
        >
          <FilePlus :size="18" />
          <span>New File</span>
        </button>
        <button
          v-if="!options?.readOnly"
          class="toolbar-button"
          title="New Folder"
          @click="handleNewFolder"
        >
          <FolderPlus :size="18" />
          <span>New Folder</span>
        </button>
        <button
          v-if="!options?.readOnly && store.selectedNodeId"
          class="toolbar-button danger"
          title="Delete"
          @click="handleDelete"
        >
          <Trash2 :size="18" />
        </button>
      </div>
      <div class="toolbar-right">
        <button
          class="toolbar-button"
          title="Refresh"
          @click="handleRefresh"
        >
          <RefreshCw :size="18" />
        </button>
        <button
          class="toolbar-button"
          title="Export JSON"
          @click="handleExport"
        >
          <Download :size="18" />
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <div class="search-input-wrapper">
        <Search :size="18" class="search-icon" />
        <input
          ref="searchInputRef"
          type="text"
          class="search-input"
          placeholder="Search files and folders..."
          @input="handleSearchInput"
        />
        <button
          v-if="store.searchQuery.length > 0"
          class="search-clear-button"
          title="Clear search"
          @click="handleClearSearch"
        >
          <X :size="18" />
        </button>
      </div>
    </div>

    <!-- Tree View Area -->
    <div class="file-tree-content">
      <div v-if="showEmptyState" class="empty-state">
        <p>No files or folders</p>
        <p class="empty-state-hint">Click "New File" or "New Folder" to get started</p>
      </div>
      <div v-else-if="noSearchResults" class="empty-state">
        <p>No files or folders match your search</p>
        <p class="empty-state-hint">Try a different search term or clear the search</p>
      </div>
      <div v-else class="tree-nodes">
        <FileTreeNode
          v-for="node in store.tree"
          :key="node.id"
          :node="node"
          :level="0"
          :is-draggable="options?.allowDragDrop ?? true"
          :max-depth="options?.maxDepth ?? 20"
        />
      </div>
    </div>

    <!-- Description Panel -->
    <div v-if="options?.showDescription" class="description-panel">
      <div v-if="selectedNode" class="description-content">
        <div class="description-header">
          <h3>{{ selectedNode.name }}</h3>
          <span class="node-type-badge">{{ selectedNode.type }}</span>
        </div>
        <div v-if="selectedNodePath" class="description-path">
          <strong>Path:</strong> {{ selectedNodePath }}
        </div>
        <div v-if="selectedNode.description" class="description-text">
          <strong>Description:</strong>
          <p>{{ selectedNode.description }}</p>
        </div>
        <div v-if="selectedNode.createdAt" class="description-meta">
          <strong>Created:</strong> {{ new Date(selectedNode.createdAt).toLocaleString() }}
        </div>
        <div v-if="selectedNode.updatedAt" class="description-meta">
          <strong>Updated:</strong> {{ new Date(selectedNode.updatedAt).toLocaleString() }}
        </div>
      </div>
      <div v-else class="description-placeholder">
        <p>Select a file or folder to view details</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-tree-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.file-tree-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  gap: 8px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 8px;
}

.toolbar-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #111827;
  transition: all 0.15s ease;
}

.toolbar-button:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.toolbar-button.danger {
  color: #ef4444;
}

.toolbar-button.danger:hover {
  background: #fef2f2;
  border-color: #ef4444;
}

/* Search Bar */
.search-bar {
  padding: 12px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #6b7280;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 8px 40px 8px 40px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
  color: #111827;
  outline: none;
  transition: all 0.15s ease;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-clear-button {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.15s ease;
}

.search-clear-button:hover {
  background: #e5e7eb;
  color: #111827;
}

.file-tree-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px;
  min-height: 300px;
}

.tree-nodes {
  width: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
  text-align: center;
}

.empty-state p {
  margin: 4px 0;
  font-size: 16px;
}

.empty-state-hint {
  font-size: 14px;
  color: #d1d5db;
}

.description-panel {
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 16px;
  min-height: 120px;
  max-height: 300px;
  overflow-y: auto;
}

.description-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.description-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.description-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.node-type-badge {
  padding: 2px 8px;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.description-path,
.description-text,
.description-meta {
  font-size: 14px;
  color: #4b5563;
}

.description-path strong,
.description-text strong,
.description-meta strong {
  color: #111827;
  font-weight: 600;
}

.description-text p {
  margin: 4px 0 0 0;
  line-height: 1.5;
}

.description-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
  font-size: 14px;
}

.compact-mode .file-tree-toolbar {
  padding: 8px;
}

.compact-mode .file-tree-content {
  padding: 8px;
}

.compact-mode .description-panel {
  padding: 12px;
  min-height: 80px;
}

/* Scrollbar styling */
.file-tree-content::-webkit-scrollbar,
.description-panel::-webkit-scrollbar {
  width: 8px;
}

.file-tree-content::-webkit-scrollbar-track,
.description-panel::-webkit-scrollbar-track {
  background: #f3f4f6;
}

.file-tree-content::-webkit-scrollbar-thumb,
.description-panel::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.file-tree-content::-webkit-scrollbar-thumb:hover,
.description-panel::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>

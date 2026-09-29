<script setup lang="ts">
import { computed } from 'vue';
import type { FileTreeNode as FileTreeNodeType } from '../types/fileTree';
import { useFileTreeStore } from '../stores/fileTreeStore';
import { useFileTreeDragDrop } from '../composables/useFileTreeDragDrop';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  File,
  FileCode,
  FileText,
  Code,
  Image,
  Braces,
  Palette,
  Settings
} from 'lucide-vue-next';
import { getFileIcon } from '../utils/fileTreeUtils';

interface Props {
  node: FileTreeNodeType;
  level?: number;
  isDraggable?: boolean;
  maxDepth?: number;
}

const props = withDefaults(defineProps<Props>(), {
  level: 0,
  isDraggable: true,
  maxDepth: 20,
});

const store = useFileTreeStore();
const dragDrop = useFileTreeDragDrop();

const isExpanded = computed(() => store.isNodeExpanded(props.node.id));
const isSelected = computed(() => store.selectedNodeId === props.node.id);
const isDragging = computed(() => dragDrop.isNodeDragging(props.node.id));
// canDrop is available for potential future use in visual feedback
const _canDrop = computed(() => dragDrop.canDropOnNode(props.node));
void _canDrop; // Suppress unused warning
const isMaxDepthReached = computed(() => props.level >= props.maxDepth);

// Check if node should be visible based on search filter
const isVisible = computed(() => {
  if (!store.filteredNodeIds) {
    return true; // No filter active, show all nodes
  }
  return store.filteredNodeIds.has(props.node.id);
});

// Check if this node or any descendant matches the search
const isMatchingNode = computed(() => {
  if (!store.filteredNodeIds || !store.searchQuery) {
    return false;
  }
  // Only highlight nodes that actually match the search (not just parents)
  const normalizedQuery = store.searchQuery.toLowerCase();
  return props.node.name.toLowerCase().includes(normalizedQuery);
});

const canRenderChildren = computed(() =>
  props.node.type === 'folder' &&
  isExpanded.value &&
  props.node.children &&
  !isMaxDepthReached.value
);

const indentStyle = computed(() => ({
  paddingLeft: `${props.level * 20}px`,
}));

const nodeClasses = computed(() => ({
  'file-tree-node': true,
  'selected': isSelected.value,
  'dragging': isDragging.value,
  'folder': props.node.type === 'folder',
  'file': props.node.type === 'file',
  'expanded': isExpanded.value,
  'matching': isMatchingNode.value,
}));

const iconComponent = computed(() => {
  if (props.node.type === 'folder') {
    return isExpanded.value ? FolderOpen : Folder;
  }

  const iconName = getFileIcon(props.node.name);
  const iconMap: Record<string, any> = {
    'file-code': FileCode,
    'file-text': FileText,
    'code': Code,
    'image': Image,
    'braces': Braces,
    'palette': Palette,
    'settings': Settings,
    'file': File,
  };

  return iconMap[iconName] || File;
});

const handleClick = () => {
  store.selectNode(props.node.id);
};

const handleDoubleClick = () => {
  if (props.node.type === 'folder') {
    store.toggleNode(props.node.id);
  }
};

const handleDragStart = (event: DragEvent) => {
  if (!props.isDraggable) return;
  dragDrop.onDragStart(event, props.node);
};

const handleDragOver = (event: DragEvent) => {
  if (!props.isDraggable) return;
  dragDrop.onDragOver(event, props.node);
};

const handleDragEnter = (event: DragEvent) => {
  if (!props.isDraggable) return;
  dragDrop.onDragEnter(event, props.node);
};

const handleDragLeave = (event: DragEvent) => {
  if (!props.isDraggable) return;
  dragDrop.onDragLeave(event);
};

const handleDrop = (event: DragEvent) => {
  if (!props.isDraggable) return;
  dragDrop.onDrop(event, props.node);
};

const handleDragEnd = (event: DragEvent) => {
  if (!props.isDraggable) return;
  dragDrop.onDragEnd(event);
};

const toggleExpand = (event: Event) => {
  event.stopPropagation();
  if (props.node.type === 'folder') {
    store.toggleNode(props.node.id);
  }
};
</script>

<template>
  <div v-if="isVisible" class="file-tree-node-wrapper">
    <div
      :class="nodeClasses"
      :style="indentStyle"
      :draggable="isDraggable"
      @click="handleClick"
      @dblclick="handleDoubleClick"
      @dragstart="handleDragStart"
      @dragover="handleDragOver"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @dragend="handleDragEnd"
    >
      <div class="node-content">
        <!-- Expand/collapse arrow for folders -->
        <div
          v-if="node.type === 'folder'"
          class="expand-arrow"
          @click="toggleExpand"
        >
          <ChevronRight v-if="!isExpanded" :size="16" />
          <ChevronDown v-else :size="16" />
        </div>
        <div v-else class="expand-arrow-spacer"></div>

        <!-- File/folder icon -->
        <div class="node-icon">
          <component :is="iconComponent" :size="18" />
        </div>

        <!-- Node name -->
        <div class="node-name">{{ node.name }}</div>
      </div>
    </div>

    <!-- Recursively render children if folder is expanded -->
    <div v-if="canRenderChildren" class="node-children">
      <FileTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :level="level + 1"
        :is-draggable="isDraggable"
        :max-depth="maxDepth"
      />
    </div>

    <!-- Max depth warning -->
    <div
      v-if="node.type === 'folder' && isExpanded && node.children && isMaxDepthReached"
      class="max-depth-warning"
      :style="{ paddingLeft: `${(level + 1) * 20}px` }"
    >
      <span class="warning-text">⚠️ Maximum depth reached</span>
    </div>
  </div>
</template>

<style scoped>
.file-tree-node-wrapper {
  user-select: none;
}

.file-tree-node {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  cursor: pointer;
  transition: background-color 0.15s ease;
  border-radius: 4px;
  margin: 2px 0;
}

.file-tree-node:hover {
  background-color: rgba(100, 100, 100, 0.1);
}

.file-tree-node.selected {
  background-color: rgba(59, 130, 246, 0.2);
  border-left: 3px solid #3b82f6;
}

.file-tree-node.dragging {
  opacity: 0.5;
  background-color: rgba(59, 130, 246, 0.1);
}

.file-tree-node.drop-target {
  background-color: rgba(34, 197, 94, 0.2);
  border: 2px dashed #22c55e;
}

.file-tree-node.drop-invalid {
  background-color: rgba(239, 68, 68, 0.1);
  border: 2px dashed #ef4444;
  cursor: not-allowed;
}

.file-tree-node.matching {
  background-color: rgba(251, 191, 36, 0.15);
  border-left: 3px solid #f59e0b;
}

.file-tree-node.matching.selected {
  background-color: rgba(251, 191, 36, 0.25);
}

.node-content {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.expand-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  cursor: pointer;
  border-radius: 3px;
  color: #4b5563;
  transition: background-color 0.15s ease;
}

.expand-arrow:hover {
  background-color: rgba(100, 100, 100, 0.15);
}

.expand-arrow-spacer {
  width: 20px;
  height: 20px;
}

.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

.file-tree-node.folder .node-icon {
  color: #f59e0b;
}

.file-tree-node.selected .node-icon {
  color: #3b82f6;
}

.node-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: #111827;
}

.node-children {
  margin-left: 0;
}

.max-depth-warning {
  padding: 4px 8px;
  margin: 2px 0;
  font-size: 12px;
  color: #f59e0b;
  font-style: italic;
}

.warning-text {
  opacity: 0.8;
}
</style>

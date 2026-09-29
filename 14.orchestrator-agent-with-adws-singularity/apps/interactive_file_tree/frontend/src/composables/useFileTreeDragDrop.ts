/**
 * File Tree Drag and Drop Composable
 * Handles drag-and-drop logic with validation
 */

import { ref, computed } from 'vue';
import type { FileTreeNode } from '../types/fileTree';
import { isDescendant, findParentNode } from '../utils/fileTreeUtils';
import { useFileTreeStore } from '../stores/fileTreeStore';

export function useFileTreeDragDrop() {
  const store = useFileTreeStore();

  const draggedNodeId = ref<string | null>(null);
  const dropTargetId = ref<string | null>(null);
  const isDraggingOver = ref(false);

  const isDragging = computed(() => draggedNodeId.value !== null);

  /**
   * Validate if a drop operation is allowed
   */
  const isValidDropTarget = (targetNode: FileTreeNode, draggedNode: FileTreeNode): boolean => {
    // Can't drop onto itself
    if (targetNode.id === draggedNode.id) {
      return false;
    }

    // Can only drop into folders
    if (targetNode.type !== 'folder') {
      return false;
    }

    // Can't drop a folder into itself or its descendants
    if (draggedNode.type === 'folder' && isDescendant(store.tree, draggedNode.id, targetNode.id)) {
      return false;
    }

    // Can't drop into a descendant
    if (isDescendant(store.tree, draggedNode.id, targetNode.id)) {
      return false;
    }

    // Check if already in the target folder (is current parent)
    const currentParent = findParentNode(store.tree, draggedNode.id);
    if (currentParent && currentParent.id === targetNode.id) {
      return false;
    }

    // If no parent and target is root, also invalid
    if (!currentParent && targetNode.id === 'root') {
      return false;
    }

    return true;
  };

  /**
   * Handle drag start
   */
  const onDragStart = (event: DragEvent, node: FileTreeNode) => {
    if (!event.dataTransfer) return;

    draggedNodeId.value = node.id;
    store.setDraggedNode(node.id);

    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('application/json', JSON.stringify({
      nodeId: node.id,
      nodeName: node.name,
      nodeType: node.type,
    }));

    // Add visual feedback to the dragged element
    if (event.target instanceof HTMLElement) {
      event.target.classList.add('dragging');
    }
  };

  /**
   * Handle drag over
   */
  const onDragOver = (event: DragEvent, node: FileTreeNode) => {
    event.preventDefault();
    if (!event.dataTransfer) return;

    const draggedNode = store.draggedNode;
    if (!draggedNode) return;

    if (isValidDropTarget(node, draggedNode)) {
      event.dataTransfer.dropEffect = 'move';
      dropTargetId.value = node.id;
    } else {
      event.dataTransfer.dropEffect = 'none';
      dropTargetId.value = null;
    }
  };

  /**
   * Handle drag enter
   */
  const onDragEnter = (event: DragEvent, node: FileTreeNode) => {
    event.preventDefault();

    const draggedNode = store.draggedNode;
    if (!draggedNode) return;

    if (isValidDropTarget(node, draggedNode)) {
      if (event.target instanceof HTMLElement) {
        event.target.classList.add('drop-target');
      }
    } else {
      if (event.target instanceof HTMLElement) {
        event.target.classList.add('drop-invalid');
      }
    }
  };

  /**
   * Handle drag leave
   */
  const onDragLeave = (event: DragEvent) => {
    if (event.target instanceof HTMLElement) {
      event.target.classList.remove('drop-target', 'drop-invalid');
    }
  };

  /**
   * Handle drop
   */
  const onDrop = (event: DragEvent, targetNode: FileTreeNode) => {
    event.preventDefault();
    event.stopPropagation();

    if (!event.dataTransfer) return;

    const draggedNode = store.draggedNode;
    if (!draggedNode) return;

    if (isValidDropTarget(targetNode, draggedNode)) {
      // Move the node
      store.moveNodeToParent(draggedNode.id, targetNode.id);
    }

    // Clean up classes
    if (event.target instanceof HTMLElement) {
      event.target.classList.remove('drop-target', 'drop-invalid');
    }

    // Reset drag state
    draggedNodeId.value = null;
    dropTargetId.value = null;
    store.setDraggedNode(null);
  };

  /**
   * Handle drag end
   */
  const onDragEnd = (event: DragEvent) => {
    // Clean up dragging class
    if (event.target instanceof HTMLElement) {
      event.target.classList.remove('dragging');
    }

    // Reset all drag state
    draggedNodeId.value = null;
    dropTargetId.value = null;
    isDraggingOver.value = false;
    store.setDraggedNode(null);

    // Clean up any remaining drop target classes
    document.querySelectorAll('.drop-target, .drop-invalid').forEach(el => {
      el.classList.remove('drop-target', 'drop-invalid');
    });
  };

  /**
   * Get CSS class for drop indicator
   */
  const getDropIndicatorClass = (nodeId: string): string => {
    if (dropTargetId.value === nodeId) {
      return 'drop-target';
    }
    return '';
  };

  /**
   * Check if a node is being dragged
   */
  const isNodeDragging = (nodeId: string): boolean => {
    return draggedNodeId.value === nodeId;
  };

  /**
   * Check if a node is a valid drop target for the currently dragged node
   */
  const canDropOnNode = (node: FileTreeNode): boolean => {
    const draggedNode = store.draggedNode;
    if (!draggedNode) return false;
    return isValidDropTarget(node, draggedNode);
  };

  return {
    // State
    isDragging,
    draggedNodeId,
    dropTargetId,
    isDraggingOver,

    // Methods
    onDragStart,
    onDragOver,
    onDragEnter,
    onDragLeave,
    onDrop,
    onDragEnd,
    isValidDropTarget,
    getDropIndicatorClass,
    isNodeDragging,
    canDropOnNode,
  };
}

/**
 * File Tree Pinia Store
 * Manages the state and actions for the file tree component
 */

import { defineStore } from 'pinia';
import type { FileTreeNode, FileTreeState } from '../types/fileTree';
import {
  findNodeById,
  addNode,
  removeNode,
  moveNode,
  generateNodeId,
  buildNodePath,
  validateNodeName,
  generateUniqueName,
  cloneTree,
  filterTreeByName,
} from '../utils/fileTreeUtils';

export const useFileTreeStore = defineStore('fileTree', {
  state: (): FileTreeState => ({
    tree: [],
    selectedNodeId: null,
    expandedNodeIds: new Set<string>(),
    draggedNodeId: null,
    searchQuery: '',
    filteredNodeIds: null,
  }),

  getters: {
    /**
     * Get the currently selected node
     */
    selectedNode(state): FileTreeNode | null {
      if (!state.selectedNodeId) {
        return null;
      }
      return findNodeById(state.tree, state.selectedNodeId);
    },

    /**
     * Check if a node is expanded
     */
    isNodeExpanded: (state) => (nodeId: string): boolean => {
      return state.expandedNodeIds.has(nodeId);
    },

    /**
     * Get a node by its ID
     */
    getNodeById: (state) => (nodeId: string): FileTreeNode | null => {
      return findNodeById(state.tree, nodeId);
    },

    /**
     * Get the path of a node
     */
    getNodePath: (state) => (nodeId: string): string => {
      return buildNodePath(state.tree, nodeId);
    },

    /**
     * Get the currently dragged node
     */
    draggedNode(state): FileTreeNode | null {
      if (!state.draggedNodeId) {
        return null;
      }
      return findNodeById(state.tree, state.draggedNodeId);
    },

    /**
     * Check if search is active
     */
    isSearchActive(state): boolean {
      return state.searchQuery.length > 0;
    },

    /**
     * Get visible node IDs (filtered or null for all)
     */
    visibleNodeIds(state): Set<string> | null {
      return state.filteredNodeIds;
    },
  },

  actions: {
    /**
     * Load tree data from JSON
     */
    loadTree(data: FileTreeNode[]): void {
      this.tree = cloneTree(data);
      this.selectedNodeId = null;
      this.expandedNodeIds.clear();
      this.draggedNodeId = null;
      this.searchQuery = '';
      this.filteredNodeIds = null;
    },

    /**
     * Select a node
     */
    selectNode(nodeId: string | null): void {
      this.selectedNodeId = nodeId;
    },

    /**
     * Toggle a node's expanded state
     */
    toggleNode(nodeId: string): void {
      const node = findNodeById(this.tree, nodeId);
      if (node && node.type === 'folder') {
        if (this.expandedNodeIds.has(nodeId)) {
          this.expandedNodeIds.delete(nodeId);
        } else {
          this.expandedNodeIds.add(nodeId);
        }
      }
    },

    /**
     * Expand a node
     */
    expandNode(nodeId: string): void {
      const node = findNodeById(this.tree, nodeId);
      if (node && node.type === 'folder') {
        this.expandedNodeIds.add(nodeId);
      }
    },

    /**
     * Collapse a node
     */
    collapseNode(nodeId: string): void {
      this.expandedNodeIds.delete(nodeId);
    },

    /**
     * Expand all nodes
     */
    expandAll(): void {
      const expandRecursive = (nodes: FileTreeNode[]) => {
        for (const node of nodes) {
          if (node.type === 'folder') {
            this.expandedNodeIds.add(node.id);
            if (node.children) {
              expandRecursive(node.children);
            }
          }
        }
      };
      expandRecursive(this.tree);
    },

    /**
     * Collapse all nodes
     */
    collapseAll(): void {
      this.expandedNodeIds.clear();
    },

    /**
     * Add a new file to the tree
     */
    addNewFile(parentId: string | null, name: string, description?: string): boolean {
      const validation = validateNodeName(name);
      if (!validation.valid) {
        console.error('Invalid file name:', validation.error);
        return false;
      }

      // Generate unique name if duplicate exists
      const uniqueName = generateUniqueName(this.tree, parentId, name);

      const newFile: FileTreeNode = {
        id: generateNodeId(),
        name: uniqueName,
        type: 'file',
        description,
        createdAt: new Date().toISOString(),
      };

      this.tree = addNode(this.tree, parentId, newFile);

      // Auto-expand parent if adding to a folder
      if (parentId) {
        this.expandNode(parentId);
      }

      return true;
    },

    /**
     * Add a new folder to the tree
     */
    addNewFolder(parentId: string | null, name: string, description?: string): boolean {
      const validation = validateNodeName(name);
      if (!validation.valid) {
        console.error('Invalid folder name:', validation.error);
        return false;
      }

      // Generate unique name if duplicate exists
      const uniqueName = generateUniqueName(this.tree, parentId, name);

      const newFolder: FileTreeNode = {
        id: generateNodeId(),
        name: uniqueName,
        type: 'folder',
        children: [],
        description,
        createdAt: new Date().toISOString(),
      };

      this.tree = addNode(this.tree, parentId, newFolder);

      // Auto-expand parent if adding to a folder
      if (parentId) {
        this.expandNode(parentId);
      }

      return true;
    },

    /**
     * Delete a node from the tree
     */
    deleteNode(nodeId: string): boolean {
      // Clear selection if deleting selected node
      if (this.selectedNodeId === nodeId) {
        this.selectedNodeId = null;
      }

      // Remove from expanded set
      this.expandedNodeIds.delete(nodeId);

      this.tree = removeNode(this.tree, nodeId);
      return true;
    },

    /**
     * Move a node to a new parent
     */
    moveNodeToParent(nodeId: string, newParentId: string | null): boolean {
      this.tree = moveNode(this.tree, nodeId, newParentId);

      // Auto-expand new parent
      if (newParentId) {
        this.expandNode(newParentId);
      }

      return true;
    },

    /**
     * Set the dragged node
     */
    setDraggedNode(nodeId: string | null): void {
      this.draggedNodeId = nodeId;
    },

    /**
     * Export the tree as JSON string
     */
    exportTree(): string {
      return JSON.stringify(this.tree, null, 2);
    },

    /**
     * Import tree from JSON string
     */
    importTree(jsonString: string): boolean {
      try {
        const data = JSON.parse(jsonString);
        if (Array.isArray(data)) {
          this.loadTree(data);
          return true;
        } else {
          console.error('Invalid JSON: expected an array');
          return false;
        }
      } catch (error) {
        console.error('Failed to parse JSON:', error);
        return false;
      }
    },

    /**
     * Clear the entire tree
     */
    clearTree(): void {
      this.tree = [];
      this.selectedNodeId = null;
      this.expandedNodeIds.clear();
      this.draggedNodeId = null;
      this.searchQuery = '';
      this.filteredNodeIds = null;
    },

    /**
     * Rename a node
     */
    renameNode(nodeId: string, newName: string): boolean {
      const validation = validateNodeName(newName);
      if (!validation.valid) {
        console.error('Invalid name:', validation.error);
        return false;
      }

      const updateName = (nodes: FileTreeNode[]): FileTreeNode[] => {
        return nodes.map(node => {
          if (node.id === nodeId) {
            return { ...node, name: newName, updatedAt: new Date().toISOString() };
          }
          if (node.children) {
            return { ...node, children: updateName(node.children) };
          }
          return node;
        });
      };

      this.tree = updateName(this.tree);
      return true;
    },

    /**
     * Set search query and update filtered nodes
     */
    setSearchQuery(query: string): void {
      this.searchQuery = query;

      if (!query || query.trim().length === 0) {
        // Clear search - reset to show all nodes
        this.filteredNodeIds = null;
      } else {
        // Filter tree and update filtered node IDs
        this.filteredNodeIds = filterTreeByName(this.tree, query);

        // Auto-expand parent folders that contain matching children
        if (this.filteredNodeIds.size > 0) {
          for (const nodeId of this.filteredNodeIds) {
            const node = findNodeById(this.tree, nodeId);
            if (node && node.type === 'folder') {
              this.expandNode(nodeId);
            }
          }
        }
      }
    },

    /**
     * Clear search and reset to full tree view
     */
    clearSearch(): void {
      this.searchQuery = '';
      this.filteredNodeIds = null;
    },
  },
});

/**
 * File Tree TypeScript Type Definitions
 * Defines the core data structures for the interactive file tree component
 */

/**
 * Type of node in the file tree
 */
export type FileType = 'file' | 'folder';

/**
 * Represents a single node in the file tree
 */
export interface FileTreeNode {
  id: string;
  name: string;
  type: FileType;
  children?: FileTreeNode[];
  description?: string;
  icon?: string;
  path?: string;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * State structure for the file tree store
 */
export interface FileTreeState {
  tree: FileTreeNode[];
  selectedNodeId: string | null;
  expandedNodeIds: Set<string>;
  draggedNodeId: string | null;
  searchQuery: string;
  filteredNodeIds: Set<string> | null;
}

/**
 * Payload for drag operations
 */
export interface DragPayload {
  nodeId: string;
  node: FileTreeNode;
}

/**
 * Target information for drop operations
 */
export interface DropTarget {
  targetId: string;
  targetNode: FileTreeNode;
  isValid: boolean;
}

/**
 * Options for adding a new node
 */
export interface AddNodeOptions {
  parentId: string | null;
  name: string;
  type: FileType;
  description?: string;
}

/**
 * Result of a tree operation
 */
export interface TreeOperationResult {
  success: boolean;
  message?: string;
  node?: FileTreeNode;
}

/**
 * Configuration options for FileTreeView component
 */
export interface FileTreeViewOptions {
  readOnly?: boolean;
  showToolbar?: boolean;
  showDescription?: boolean;
  compactMode?: boolean;
  maxDepth?: number;
  allowDragDrop?: boolean;
}

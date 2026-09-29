/**
 * File Tree Utility Functions
 * Provides helper functions for tree manipulation and file type detection
 */

import type { FileTreeNode } from '../types/fileTree';

/**
 * Icon mappings for different file types
 */
const FILE_ICON_MAP: Record<string, string> = {
  // Programming languages
  '.py': 'file-code',
  '.ts': 'file-code',
  '.tsx': 'file-code',
  '.js': 'file-code',
  '.jsx': 'file-code',
  '.vue': 'file-code',
  '.java': 'file-code',
  '.cpp': 'file-code',
  '.c': 'file-code',
  '.go': 'file-code',
  '.rs': 'file-code',
  '.rb': 'file-code',
  '.php': 'file-code',

  // Markup and data
  '.json': 'braces',
  '.xml': 'file-code',
  '.yaml': 'file-text',
  '.yml': 'file-text',
  '.toml': 'file-text',

  // Documentation
  '.md': 'file-text',
  '.txt': 'file-text',
  '.doc': 'file-text',
  '.docx': 'file-text',
  '.pdf': 'file-text',

  // Styling
  '.css': 'palette',
  '.scss': 'palette',
  '.sass': 'palette',
  '.less': 'palette',

  // Markup
  '.html': 'code',
  '.htm': 'code',

  // Images
  '.png': 'image',
  '.jpg': 'image',
  '.jpeg': 'image',
  '.gif': 'image',
  '.svg': 'image',
  '.ico': 'image',

  // Config
  '.env': 'settings',
  '.config': 'settings',
  '.conf': 'settings',

  // Default
  'default': 'file',
};

/**
 * Get the appropriate icon name for a file based on its extension
 */
export function getFileIcon(fileName: string): string {
  const extension = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
  return FILE_ICON_MAP[extension] || FILE_ICON_MAP['default'];
}

/**
 * Find a node by its ID in the tree
 */
export function findNodeById(tree: FileTreeNode[], id: string): FileTreeNode | null {
  for (const node of tree) {
    if (node.id === id) {
      return node;
    }
    if (node.children && node.children.length > 0) {
      const found = findNodeById(node.children, id);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

/**
 * Find the parent node of a given node ID
 */
export function findParentNode(tree: FileTreeNode[], nodeId: string, parent: FileTreeNode | null = null): FileTreeNode | null {
  for (const node of tree) {
    if (node.id === nodeId) {
      return parent;
    }
    if (node.children && node.children.length > 0) {
      const found = findParentNode(node.children, nodeId, node);
      if (found !== null) {
        return found;
      }
    }
  }
  return null;
}

/**
 * Check if a node is a descendant of another node
 */
export function isDescendant(tree: FileTreeNode[], ancestorId: string, descendantId: string): boolean {
  const ancestor = findNodeById(tree, ancestorId);
  if (!ancestor || !ancestor.children) {
    return false;
  }

  const checkChildren = (nodes: FileTreeNode[]): boolean => {
    for (const node of nodes) {
      if (node.id === descendantId) {
        return true;
      }
      if (node.children && checkChildren(node.children)) {
        return true;
      }
    }
    return false;
  };

  return checkChildren(ancestor.children);
}

/**
 * Add a new node to the tree at the specified parent
 */
export function addNode(tree: FileTreeNode[], parentId: string | null, node: FileTreeNode): FileTreeNode[] {
  if (parentId === null) {
    // Add to root
    return [...tree, node];
  }

  const addToParent = (nodes: FileTreeNode[]): FileTreeNode[] => {
    return nodes.map(n => {
      if (n.id === parentId) {
        return {
          ...n,
          children: [...(n.children || []), node],
        };
      }
      if (n.children) {
        return {
          ...n,
          children: addToParent(n.children),
        };
      }
      return n;
    });
  };

  return addToParent(tree);
}

/**
 * Remove a node from the tree
 */
export function removeNode(tree: FileTreeNode[], nodeId: string): FileTreeNode[] {
  return tree
    .filter(node => node.id !== nodeId)
    .map(node => ({
      ...node,
      children: node.children ? removeNode(node.children, nodeId) : undefined,
    }));
}

/**
 * Move a node to a new parent
 */
export function moveNode(tree: FileTreeNode[], nodeId: string, newParentId: string | null): FileTreeNode[] {
  // First, find and extract the node
  const nodeToMove = findNodeById(tree, nodeId);
  if (!nodeToMove) {
    return tree;
  }

  // Remove the node from its current position
  let updatedTree = removeNode(tree, nodeId);

  // Add it to the new parent
  updatedTree = addNode(updatedTree, newParentId, nodeToMove);

  return updatedTree;
}

/**
 * Flatten the tree into a single array (useful for search)
 */
export function flattenTree(tree: FileTreeNode[]): FileTreeNode[] {
  const result: FileTreeNode[] = [];

  const traverse = (nodes: FileTreeNode[]) => {
    for (const node of nodes) {
      result.push(node);
      if (node.children) {
        traverse(node.children);
      }
    }
  };

  traverse(tree);
  return result;
}

/**
 * Generate a unique ID for a new node
 */
export function generateNodeId(): string {
  return `node-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Build the full path for a node
 */
export function buildNodePath(tree: FileTreeNode[], nodeId: string): string {
  const path: string[] = [];

  const findPath = (nodes: FileTreeNode[], targetId: string, currentPath: string[]): boolean => {
    for (const node of nodes) {
      const newPath = [...currentPath, node.name];
      if (node.id === targetId) {
        path.push(...newPath);
        return true;
      }
      if (node.children && findPath(node.children, targetId, newPath)) {
        return true;
      }
    }
    return false;
  };

  findPath(tree, nodeId, []);
  return path.join('/');
}

/**
 * Validate a node name
 */
export function validateNodeName(name: string): { valid: boolean; error?: string } {
  if (!name || name.trim().length === 0) {
    return { valid: false, error: 'Name cannot be empty' };
  }

  if (name.length > 255) {
    return { valid: false, error: 'Name cannot exceed 255 characters' };
  }

  // Check for invalid characters (basic validation)
  const invalidChars = /[<>:"|?*]/;
  if (invalidChars.test(name)) {
    return { valid: false, error: 'Name contains invalid characters' };
  }

  return { valid: true };
}

/**
 * Check if a name already exists among siblings
 */
export function nameExistsInParent(tree: FileTreeNode[], parentId: string | null, name: string): boolean {
  let siblings: FileTreeNode[];

  if (parentId === null) {
    siblings = tree;
  } else {
    const parent = findNodeById(tree, parentId);
    if (!parent || !parent.children) {
      return false;
    }
    siblings = parent.children;
  }

  return siblings.some(node => node.name === name);
}

/**
 * Generate a unique name by appending a number if the name already exists
 */
export function generateUniqueName(tree: FileTreeNode[], parentId: string | null, baseName: string): string {
  let name = baseName;
  let counter = 1;

  while (nameExistsInParent(tree, parentId, name)) {
    // Extract extension if it exists
    const lastDot = baseName.lastIndexOf('.');
    if (lastDot > 0) {
      const nameWithoutExt = baseName.substring(0, lastDot);
      const ext = baseName.substring(lastDot);
      name = `${nameWithoutExt} (${counter})${ext}`;
    } else {
      name = `${baseName} (${counter})`;
    }
    counter++;
  }

  return name;
}

/**
 * Get the depth of a node in the tree
 */
export function getNodeDepth(tree: FileTreeNode[], nodeId: string): number {
  const findDepth = (nodes: FileTreeNode[], targetId: string, currentDepth: number): number => {
    for (const node of nodes) {
      if (node.id === targetId) {
        return currentDepth;
      }
      if (node.children) {
        const depth = findDepth(node.children, targetId, currentDepth + 1);
        if (depth !== -1) {
          return depth;
        }
      }
    }
    return -1;
  };

  return findDepth(tree, nodeId, 0);
}

/**
 * Clone a tree (deep copy)
 */
export function cloneTree(tree: FileTreeNode[]): FileTreeNode[] {
  return JSON.parse(JSON.stringify(tree));
}

/**
 * Get all parent IDs for a given node
 * Used to ensure parent folders are visible when children match search
 */
export function getParentIds(tree: FileTreeNode[], nodeId: string): string[] {
  const parentIds: string[] = [];

  const findParents = (nodes: FileTreeNode[], targetId: string, ancestors: string[]): boolean => {
    for (const node of nodes) {
      if (node.id === targetId) {
        parentIds.push(...ancestors);
        return true;
      }
      if (node.children) {
        const found = findParents(node.children, targetId, [...ancestors, node.id]);
        if (found) {
          return true;
        }
      }
    }
    return false;
  };

  findParents(tree, nodeId, []);
  return parentIds;
}

/**
 * Filter tree by name (case-insensitive, partial matching)
 * Returns a Set of node IDs that match the query, including parent IDs for visibility
 */
export function filterTreeByName(tree: FileTreeNode[], query: string): Set<string> {
  const matchingIds = new Set<string>();

  if (!query || query.trim().length === 0) {
    return matchingIds;
  }

  const normalizedQuery = query.toLowerCase().trim();
  const flatNodes = flattenTree(tree);

  // Find all nodes that match the query
  for (const node of flatNodes) {
    if (node.name.toLowerCase().includes(normalizedQuery)) {
      matchingIds.add(node.id);

      // Add all parent IDs to maintain hierarchy visibility
      const parentIds = getParentIds(tree, node.id);
      for (const parentId of parentIds) {
        matchingIds.add(parentId);
      }
    }
  }

  return matchingIds;
}

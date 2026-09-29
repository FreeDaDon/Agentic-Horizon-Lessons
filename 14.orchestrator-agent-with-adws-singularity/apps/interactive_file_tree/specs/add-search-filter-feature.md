# Plan: Add Search/Filter Feature to Interactive File Tree

## Task Description
Add a search/filter feature to the interactive file tree application that allows users to filter files and folders by name. The feature will include a search input field positioned at the top of the file tree that filters visible nodes in real-time as the user types. The search will be case-insensitive and match partial file/folder names, showing only nodes that match the search query along with their parent paths.

## Objective
Implement a real-time search functionality that enhances the user experience by allowing quick navigation and filtering of files/folders in large directory trees. The search should be intuitive, performant, and seamlessly integrated with the existing UI.

## Problem Statement
In large file trees with many nested files and folders, users need an efficient way to locate specific items without manually expanding folders and scanning through the hierarchy. Currently, the application lacks a search mechanism, making it difficult to quickly find files or folders when dealing with complex directory structures.

## Solution Approach
The solution will add a search input field to the toolbar area and implement filtering logic in the Pinia store. The filtering approach will:
1. Match nodes based on partial, case-insensitive name matching
2. Show matching nodes along with their parent hierarchy (breadcrumb trail)
3. Auto-expand parent folders to reveal matching children
4. Provide visual feedback for filtered results
5. Allow easy clearing of search to restore full tree view

The implementation will leverage existing utility functions (like `flattenTree`) and extend the store with search-specific state and actions.

## Relevant Files
The following files will be modified to implement the search feature:

- **frontend/src/components/FileTreeView.vue** - Main container component where the search input will be added to the toolbar
- **frontend/src/stores/fileTreeStore.ts** - Pinia store that will be extended with search state (searchQuery, filteredNodeIds) and search actions
- **frontend/src/utils/fileTreeUtils.ts** - Utility functions file where we'll add search/filter helper functions
- **frontend/src/types/fileTree.ts** - Type definitions where we'll add search-related types to FileTreeState

### New Files
No new files will be created. All functionality will be added to existing files.

## Implementation Phases

### Phase 1: Foundation
Add the necessary type definitions and state management infrastructure for search functionality. This includes extending the store state with search-related properties and creating utility functions for filtering.

### Phase 2: Core Implementation
Implement the search/filter logic in the store and utility functions. Create actions to handle search queries, filter the tree, and manage expanded state based on search results.

### Phase 3: Integration & Polish
Add the search input UI component to the FileTreeView toolbar, wire up the reactive search behavior, and ensure proper visual feedback for filtered results. Add keyboard shortcuts and UX enhancements.

## Step by Step Tasks

### 1. Update Type Definitions
- Add `searchQuery` (string) to `FileTreeState` interface in `types/fileTree.ts`
- Add `filteredNodeIds` (Set<string> | null) to `FileTreeState` to track nodes that match search
- Consider adding a boolean `isSearchActive` computed property indicator

### 2. Add Search Utility Functions
- Create `filterTreeByName(tree: FileTreeNode[], query: string): Set<string>` function in `fileTreeUtils.ts`
  - Use case-insensitive matching with `toLowerCase()`
  - Match partial names using `includes()`
  - Return a Set of node IDs that match the query
  - Include parent node IDs in the result set to maintain hierarchy visibility
- Create `getParentIds(tree: FileTreeNode[], nodeId: string): string[]` helper function
  - Recursively find and return all parent IDs for a given node
  - Used to ensure parent folders are visible when children match search

### 3. Extend Pinia Store with Search State
- Add `searchQuery: ''` to the initial state in `fileTreeStore.ts`
- Add `filteredNodeIds: null` to the initial state (null means no filter active)
- Create computed getter `isSearchActive()` that returns `searchQuery.length > 0`
- Create computed getter `visibleNodeIds()` that returns filtered IDs or null

### 4. Implement Store Search Actions
- Create `setSearchQuery(query: string)` action
  - Update `searchQuery` state
  - If query is empty, set `filteredNodeIds` to null and collapse unnecessary nodes
  - If query has content, call filter utility and update `filteredNodeIds`
  - Auto-expand parent folders that contain matching children
- Create `clearSearch()` action
  - Reset `searchQuery` to empty string
  - Set `filteredNodeIds` to null
  - Optionally collapse all nodes or restore previous expanded state
- Update existing actions to respect search state
  - Modify node visibility logic to check if search is active

### 5. Add Search Input to FileTreeView Component
- Import `Search` and `X` icons from `lucide-vue-next` in `FileTreeView.vue`
- Add a search input field in the toolbar section (above the tree view area)
  - Position it as a full-width input or in a dedicated search bar area
  - Add placeholder text: "Search files and folders..."
  - Bind input value to `store.searchQuery` with v-model
  - Add debouncing (150-300ms) to avoid excessive filtering on every keystroke
- Add a clear button (X icon) that appears when search has text
  - Only visible when `searchQuery.length > 0`
  - Clicking it calls `store.clearSearch()`

### 6. Update FileTreeNode Rendering Logic
- Modify `FileTreeNode.vue` to accept and respect filtered state
  - Add conditional rendering based on `store.filteredNodeIds`
  - Show node if: `!store.filteredNodeIds || store.filteredNodeIds.has(node.id)`
  - Add a CSS class for filtered/highlighted nodes (optional visual indicator)
- Ensure parent folders automatically expand when children match
  - Check if any children are in `filteredNodeIds` and auto-expand parent

### 7. Add Visual Feedback for Search
- Add styling for the search input in `FileTreeView.vue`
  - Use consistent styling with existing toolbar elements
  - Add focus states and proper spacing
  - Ensure responsive design on mobile devices
- Add optional highlighting for matched text in node names
  - Consider adding a visual indicator (e.g., subtle background color) for matching nodes
  - Could use a computed property to identify the matching portion of the name
- Add empty state message when search yields no results
  - "No files or folders match your search"
  - Include the current search query in the message

### 8. Implement Keyboard Shortcuts
- Add keyboard shortcut for focusing search input
  - Cmd/Ctrl + F to focus the search field
  - ESC to clear search and unfocus input
- Update `handleKeyDown` in `FileTreeView.vue` to handle new shortcuts
  - Check for Cmd/Ctrl + F key combination
  - Prevent default browser search behavior

### 9. Test Search Functionality
- Test with empty tree (should show empty state)
- Test with single-level tree (no nesting)
- Test with deeply nested tree structure
- Test partial name matching (e.g., "test" matches "test.js", "my-test-file.txt")
- Test case-insensitivity (e.g., "TEST" matches "test.js")
- Test special characters in search and file names
- Test clearing search restores original tree view
- Test search with already expanded/collapsed nodes
- Test performance with large trees (100+ nodes)

### 10. Add Search State Persistence (Optional Enhancement)
- Consider storing search query in localStorage
- Restore search state on component mount
- This is optional but improves UX for repeated sessions

## Testing Strategy

### Manual Testing
1. **Basic Search Functionality**
   - Type in search input and verify nodes filter correctly
   - Verify case-insensitive matching works
   - Verify partial name matching works
   - Verify clear button removes filter

2. **Tree Interaction During Search**
   - Verify parent folders auto-expand to show matching children
   - Verify selecting filtered nodes works correctly
   - Verify drag-and-drop still functions during search (if applicable)
   - Verify CRUD operations (add/delete) work with active search

3. **Edge Cases**
   - Search with special characters (@, #, -, etc.)
   - Search with very long query strings
   - Search that matches all nodes
   - Search that matches no nodes
   - Rapid typing (test debouncing)
   - Multiple consecutive searches

4. **Performance Testing**
   - Load sample tree with 100+ nodes
   - Test search response time
   - Verify smooth typing experience (no lag)
   - Check memory usage with repeated searches

### Automated Testing Approach
While the current project doesn't include automated tests, future test coverage should include:
- Unit tests for `filterTreeByName()` utility function
- Unit tests for `getParentIds()` helper function
- Store action tests for `setSearchQuery()` and `clearSearch()`
- Component tests for search input rendering and user interactions

## Acceptance Criteria
The feature will be considered complete when all of the following criteria are met:

1. **Search Input Visible** - A search input field is displayed at the top of the file tree interface
2. **Real-time Filtering** - Typing in the search field immediately filters the visible nodes (with debouncing)
3. **Case-Insensitive** - Search matching is case-insensitive (e.g., "TEST" matches "test.js")
4. **Partial Matching** - Search matches partial names (e.g., "conf" matches "config.json")
5. **Parent Visibility** - When a child node matches, all parent folders in the path are visible and expanded
6. **Clear Functionality** - A clear button (X icon) is visible when search has text and clears the search when clicked
7. **Empty State** - When search yields no results, a helpful message is displayed
8. **Keyboard Support** - Cmd/Ctrl + F focuses the search input, ESC clears search
9. **No Regression** - All existing functionality (expand/collapse, select, drag-drop, CRUD) continues to work during search
10. **Performance** - Search remains responsive with trees containing 100+ nodes
11. **Accessibility** - Search input has proper ARIA labels and keyboard navigation

## Validation Commands
Execute these commands to validate the task is complete:

- `cd frontend && npm run type-check` - Verify TypeScript types are correct with no errors
- `cd frontend && npm run build` - Ensure the application builds successfully without errors
- `cd frontend && npm run dev` - Start the development server and manually test search functionality
- Test search with sample data:
  1. Load the app at http://localhost:5180
  2. Type "test" in the search field
  3. Verify only files/folders with "test" in the name are visible
  4. Verify parent folders are expanded to show matching children
  5. Click the clear button and verify full tree is restored
  6. Test keyboard shortcut Cmd/Ctrl + F to focus search
  7. Test ESC key to clear search

## Notes

### Performance Considerations
- Implement debouncing on search input (300ms) to reduce excessive re-renders
- Use Set data structure for filteredNodeIds for O(1) lookup performance
- Consider memoization if filtering becomes expensive with very large trees

### UX Enhancements (Future)
- Add search history dropdown (recent searches)
- Add advanced filters (by file type, date modified, etc.)
- Add search result count display ("5 results found")
- Highlight matching text within node names
- Add option to search file contents (not just names)

### Dependencies
- No new dependencies required
- Uses existing Lucide icons for search and clear buttons
- Leverages existing Pinia store infrastructure
- Uses existing TypeScript and Vue 3 setup

### Implementation Time Estimate
This is a medium complexity feature that should take approximately:
- Type definitions and utility functions: 30 minutes
- Store state and actions: 45 minutes
- UI component integration: 45 minutes
- Styling and visual feedback: 30 minutes
- Testing and bug fixes: 60 minutes
- Total estimated time: 3-4 hours

### Related Patterns in Codebase
- The store already has `selectedNodeId` pattern - search will follow similar state management
- The `flattenTree()` utility exists and can be leveraged for search
- The toolbar already has buttons with icons - search input will match this style
- The component already uses keyboard event handlers - can extend for search shortcuts

# Interactive File Tree

A Vue 3 + TypeScript interactive file tree component with drag-and-drop support, built using Vite and Pinia.

## Features

- **Hierarchical File Tree Display**: Navigate through files and folders with expandable/collapsible nodes
- **Drag and Drop**: Reorganize files and folders by dragging them to new locations
- **CRUD Operations**: Create new files and folders, delete items
- **File Type Icons**: Automatic icon assignment based on file extensions (via Lucide icons)
- **Description Panel**: View details of selected files including path and description
- **Export/Import**: Export the tree structure as JSON
- **Keyboard Support**: Delete key to remove selected items
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Automatic dark mode based on system preferences

## Quick Start

### Using the start script

```bash
./start_fe.sh
```

### Manual setup

```bash
cd frontend
npm install
npm run dev
```

The application will start on **http://localhost:5180**

## Project Structure

```
apps/interactive_file_tree/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileTreeNode.vue    # Recursive tree node component
│   │   │   └── FileTreeView.vue    # Main container component
│   │   ├── composables/
│   │   │   └── useFileTreeDragDrop.ts  # Drag-and-drop logic
│   │   ├── stores/
│   │   │   └── fileTreeStore.ts    # Pinia state management
│   │   ├── types/
│   │   │   └── fileTree.ts         # TypeScript definitions
│   │   ├── utils/
│   │   │   └── fileTreeUtils.ts    # Tree manipulation utilities
│   │   ├── styles/
│   │   │   └── fileTree.css        # Global styles
│   │   ├── data/
│   │   │   └── sampleFileTree.json # Sample data for demo
│   │   ├── App.vue                 # Root component
│   │   └── main.ts                 # Entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── start_fe.sh                     # Startup script
└── README.md
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server on port 5180 |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run type-check` | Run TypeScript type checking |

## Component Usage

### Basic Usage

```vue
<template>
  <FileTreeView />
</template>

<script setup lang="ts">
import FileTreeView from './components/FileTreeView.vue';
</script>
```

### With Custom Data

```vue
<template>
  <FileTreeView :initial-data="myTreeData" />
</template>

<script setup lang="ts">
import FileTreeView from './components/FileTreeView.vue';
import type { FileTreeNode } from './types/fileTree';

const myTreeData: FileTreeNode[] = [
  {
    id: 'folder-1',
    name: 'My Folder',
    type: 'folder',
    children: [
      {
        id: 'file-1',
        name: 'document.txt',
        type: 'file',
        description: 'A sample document'
      }
    ]
  }
];
</script>
```

### Component Options

```vue
<FileTreeView
  :initial-data="treeData"
  :options="{
    readOnly: false,
    showToolbar: true,
    showDescription: true,
    compactMode: false,
    maxDepth: 20,
    allowDragDrop: true
  }"
/>
```

## Dependencies

- **Vue 3**: Progressive JavaScript framework
- **Pinia**: State management for Vue
- **Vite**: Next-generation frontend tooling
- **TypeScript**: Type-safe JavaScript
- **Lucide Vue Next**: Beautiful and consistent icons

## Interactions

| Action | Result |
|--------|--------|
| Click | Select node |
| Double-click folder | Expand/collapse |
| Drag file/folder | Move to another folder |
| New File button | Create file in selected folder |
| New Folder button | Create folder in selected folder |
| Delete button | Remove selected item |
| Delete key | Remove selected item |
| Export button | Download tree as JSON |

## Configuration

The app runs on port **5180** by default to avoid conflicts with other applications. This can be changed in:

- `vite.config.ts` - `server.port`
- `package.json` - dev script `--port` flag

## License

MIT

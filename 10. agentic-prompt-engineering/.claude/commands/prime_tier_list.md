# Agentic Prompt Section Tier List Guide

Execute the `Workflow` then `Report` your understanding. Your mission is to understand the interactive 2D grid tier list application so we can make new updates to the system.

## Codebase Structure

Take note of these files, but do not read them.

```
apps/prompt_tier_list/
├── README.md                           # Project documentation
├── package.json                        # Dependencies and scripts
├── index.html                          # Entry HTML file
├── src/
│   ├── App.vue                        # Main application entry, coordinates grid and pool
│   ├── main.ts                        # Application bootstrap
│   ├── components/
│   │   ├── TierGrid.vue              # 5x5 grid system with axis labels
│   │   ├── GridCell.vue              # Individual grid cells with stacking/reordering
│   │   ├── EntityPool.vue            # Available entities pool (drag source)
│   │   └── DraggableEntity.vue       # Individual draggable prompt sections
│   ├── constants/
│   │   └── entities.ts               # Gradable prompt sections and formats
│   ├── types/
│   │   └── index.ts                  # TypeScript interfaces (Entity, GridPosition, DragData)
│   ├── composables/
│   │   └── useDragAndDrop.ts         # Drag & drop logic composable
│   └── assets/
│       └── global.css                # Dracula-inspired theme with CSS variables
```

## Workflow

### 1. Understanding the Grid System
- **5x5 Grid Layout**: Interactive cells for placing entities
- **X-axis (Horizontal)**: "Beginner" (left) to "Expert" (right) - represents skill level required
- **Y-axis (Vertical)**: "Useful" (top) to "Useless" (bottom) - represents usefulness
- **Each cell can stack multiple entities**: Entities can be reordered within cells

### 2. Read Essential Files
- IMPORTANT: Read these files **exclusively**:
  - `README.md` for project overview
  - `apps/prompt_tier_list/README.md` for project overview
  - `apps/prompt_tier_list/src/App.vue` to understand main application structure
  - `apps/prompt_tier_list/package.json` to understand dependencies
  - `apps/prompt_tier_list/index.html` to understand entry point

### 3. How the System Works

#### Drag and Drop Flow
1. **From Pool to Grid**: Drag entities from "Available Prompt Sections" to any grid cell
2. **Between Grid Cells**: Move entities between different grid positions
3. **Back to Pool**: Return misplaced entities by dragging back to the pool
4. **Within Cell Reordering**: Drag entities within the same cell to reorder stack

#### State Management
- Grid state managed in `TierGrid.vue` using Vue reactive refs
- Each cell tracks its own entities array
- Pool tracks placed vs available entities
- Uses native HTML5 drag/drop with JSON data transfer

#### Visual Feedback
- Green labels for axes (Beginner, Expert, Useful, Useless)
- Purple styling for H1 (# Title) and H2 sections (##)
- Position-based purple gradient (stronger towards Expert + Useful)
- Hover states show drop zones
- Dragging opacity changes for feedback

### 4. Entity Categories
The 12 gradable entities represent prompt engineering sections:
- `# Title` - H1 header with purple theming
- `## Metadata`, `## Purpose`, `## Variables`, etc. - H2 sections with purple theming
- Each can be placed anywhere on the usefulness/expertise grid

### 5. Customization Points
- Theme colors in `global.css` using CSS variables
- Grid size constant in `TierGrid.vue` (currently 5x5)
- Entity list in `constants/entities.ts`
- Drag/drop behavior in `useDragAndDrop.ts`

### 6. Start the Application
- Navigate to the app: `cd apps/prompt_tier_list`
- Install dependencies: `bun install`
- Run development server: `bun run dev`
- Open browser: http://localhost:5173/


## Report

Report your understanding of the system and the entities in the grid.
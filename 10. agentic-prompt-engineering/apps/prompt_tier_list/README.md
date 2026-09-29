# Agentic Prompt Tier List

An interactive 2D grid tier list application for categorizing prompt engineering components by expertise level and usefulness.

## Features

- **5x5 Interactive Grid**: Drag and drop entities to rank them
- **Two Axes**:
  - X-axis: Beginner → Expert (skill level required)
  - Y-axis: Useful → Useless (practical value)
- **Three Entity Types**:
  - **H1 Headers** (`# Title`) - Purple themed
  - **H2 Sections** (`## Metadata`, `## Purpose`, etc.) - Purple themed
  - **Prompt Formats** (`*.md` files) - Sky blue themed
- **Persistent State**: Positions saved to localStorage
- **Visual Feedback**: Purple gradient intensifies toward Expert + Useful quadrant
- **Reset Functionality**: Clear button to restore default state

## Entity Categories

### Prompt Sections (Purple)
- `# Title` - Main prompt title
- `## Metadata` - Prompt metadata
- `## Purpose` - Purpose statement
- `## Variables` - Input variables
- `## Instructions` - Core instructions
- `## Relevant Files` - File references
- `## Codebase Structure` - Structure overview
- `## Workflow` - Workflow steps
- `## Expertise` - Required expertise
- `## Template` - Template patterns
- `## Examples` - Usage examples
- `## Report` - Output report

### Prompt Formats (Sky Blue)
- `high_level_prompt.md` - One-off, adhoc prompts
- `workflow_prompt.md` - Input-Work-Output workflow
- `higher_order_prompt.md` - Accepts other prompts as input
- `control_flow_prompt.md` - Conditional/loop workflows
- `delegate_prompt.md` - Delegates to other agents
- `template_metaprompt.md` - Creates new prompts
- `self_improving_prompt.md` - Self-updating prompts

## Development

```bash
# Install dependencies
bun install

# Run development server
bun run dev

# Build for production
bun run build

# Preview production build
bun run preview
```

## Tech Stack

- Vue 3 with Composition API
- TypeScript
- Vite
- Dracula-inspired theme
- Native HTML5 Drag & Drop API

## Usage

1. Drag entities from "Available Prompt Sections" pool
2. Drop them onto grid cells based on your assessment
3. Reorder within cells by dragging
4. Return to pool by dragging back
5. Use reset button (×) to clear all placements

## Grid Interpretation

- **Top-Right** (Expert + Useful): Advanced techniques with high value
- **Top-Left** (Beginner + Useful): Simple but effective basics
- **Bottom-Right** (Expert + Useless): Complex but low-value items
- **Bottom-Left** (Beginner + Useless): Simple and low-value items
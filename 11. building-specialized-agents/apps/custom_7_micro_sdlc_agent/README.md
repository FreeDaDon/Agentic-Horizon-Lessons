# Micro SDLC Agent

> 🚀 Plan → Build → Review → Ship

A specialized agent system for orchestrating engineering work through a micro Software Development Life Cycle (SDLC) workflow. This application provides a kanban board interface for managing tickets that progress through automated planning, building, and review stages powered by Claude Agent SDK agents.

## Overview

The Micro SDLC Agent implements a complete engineering workflow with three specialized agents:

1. **Planner Agent** - Analyzes requirements and creates detailed implementation plans
2. **Builder Agent** - Executes the plan and implements the solution
3. **Reviewer Agent** - Reviews the implementation against the plan and provides comprehensive feedback

## Features

- **Visual Kanban Board** - Drag-and-drop interface with stage-based workflow
- **Automated Workflow** - Agents automatically handle plan → build → review progression
- **Real-time Updates** - WebSocket connections for live progress monitoring
- **Agent Message Tracking** - Complete visibility into agent thinking and tool usage
- **Multiple Model Support** - Choose between Sonnet (faster) and Opus (smarter)
- **Persistent Storage** - SQLite database for ticket and session management

## Architecture

```
apps/custom_7_micro_sdlc_agent/
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── db/
│   │   └── database.py           # SQLite operations
│   └── modules/
│       └── agent_orchestrator.py  # Agent execution logic
├── frontend/
│   ├── src/
│   │   ├── App.vue                # Main kanban board
│   │   ├── components/
│   │   │   ├── TicketCard.vue    # Ticket display
│   │   │   ├── CreateTicketModal.vue
│   │   │   └── TicketDetailsModal.vue
│   │   └── stores/
│   │       └── tickets.js         # Pinia state management
│   └── package.json
├── system_prompts/
│   ├── PLANNER_AGENT_SYSTEM_PROMPT.md
│   └── REVIEWER_AGENT_SYSTEM_PROMPT.md
├── user_prompts/
│   ├── PLANNER_AGENT_USER_PROMPT.md
│   ├── BUILDER_AGENT_USER_PROMPT.md
│   └── REVIEWER_AGENT_USER_PROMPT.md
├── plans/                         # Generated plan files
└── reviews/                       # Generated review files
```

## Installation

### Backend Setup

```bash
cd apps/custom_7_micro_sdlc_agent/backend
uv sync

# Important: WebSocket support requires uvicorn[standard]
# If you see WebSocket errors, run:
uv pip install 'uvicorn[standard]' websockets
```

### Frontend Setup

```bash
cd apps/custom_7_micro_sdlc_agent/frontend
npm install
```

## Running the Application

### Start Backend (Terminal 1)

```bash
cd apps/custom_7_micro_sdlc_agent/backend
uv run python main.py
```

The backend will be available at `http://127.0.0.1:8001`

### Start Frontend (Terminal 2)

```bash
cd apps/custom_7_micro_sdlc_agent/frontend
npm run dev
```

Open your browser to `http://127.0.0.1:5174`

## Workflow Stages

### 1. **Idle** (Light Gray)
- Initial state for new tickets
- Can be dragged to Plan or Archived

### 2. **Plan** (Light Blue)
- Planner agent analyzes requirements
- Creates detailed implementation plan
- Saves plan to `plans/` directory

### 3. **Build** (Light Green)
- Builder agent reads the plan
- Implements the solution
- Reports changes via git diff

### 4. **Review** (Light Yellow)
- Reviewer agent compares implementation to plan
- Assesses code quality
- Creates comprehensive review document

### 5. **Shipped** (Light Purple)
- Successfully completed workflow
- Can be moved to Archived

### 6. **Errored** (Light Red)
- Workflow encountered an error
- Can be reset to Idle or Archived

### 7. **Archived** (Light Gray)
- Completed or cancelled tickets

## Drag & Drop Rules

- **Can be moved manually:**
  - Idle → Plan, Archived
  - Shipped → Archived
  - Errored → Idle, Archived
  - Archived → Idle

- **Cannot be moved manually:**
  - Plan, Build, Review stages (automated progression only)

## Creating a Ticket

1. Click the **"+ New Ticket"** button in the Idle column
2. Fill in the form:
   - **Title**: Brief description of the task
   - **Model**: Choose Sonnet (faster) or Opus (smarter)
   - **Codebase Path**: Working directory (default: ".")
   - **User Request Prompt**: Detailed requirements
3. Click "Create Ticket"

## Starting the Workflow

1. Drag a ticket from **Idle** to **Plan**
2. The system automatically:
   - Runs the Planner Agent
   - Moves to Build stage
   - Runs the Builder Agent
   - Moves to Review stage
   - Runs the Reviewer Agent
   - Moves to Shipped on success

## Agent Details

### Planner Agent
- **Purpose**: Strategic planning and solution design
- **Output**: Markdown plan in `plans/` directory
- **Restrictions**: Can only write to `plans/`

### Builder Agent
- **Purpose**: Execute the plan and implement the solution
- **Input**: Plan file path
- **Output**: Git diff of changes

### Reviewer Agent
- **Purpose**: Quality assessment and feedback
- **Input**: Plan file path
- **Output**: Review document in `reviews/`
- **Restrictions**: Can only write to `reviews/`

## Database Schema

### Tickets Table
```sql
- id: INTEGER PRIMARY KEY
- title: TEXT
- content_user_request_prompt: TEXT
- content_plan_response: TEXT
- content_build_response: TEXT
- content_review_response: TEXT
- agent_messages: JSON (array of messages)
- plan_path: TEXT
- stage: TEXT
- model: TEXT (sonnet/opus)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- plan/build/review_claude_code_session_id: TEXT
- total_plan/build/review_messages: INTEGER
- total_plan/build/review_tool_calls: INTEGER
- parent_codebase_path: TEXT
```

## API Endpoints

- `GET /health` - Health check
- `GET /session` - Get session information
- `GET /tickets` - List all tickets
- `GET /tickets/{id}` - Get specific ticket
- `POST /tickets` - Create new ticket
- `PUT /tickets/{id}/stage` - Update ticket stage
- `WS /ws` - WebSocket for real-time updates

## Real-time Features

The application uses WebSocket connections to provide real-time updates:

- Ticket creation notifications
- Stage transition updates
- Agent message streaming
- Workflow status changes

## Tips for Best Results

1. **Clear Requirements**: Provide detailed, unambiguous requirements in your prompts
2. **Appropriate Model Selection**:
   - Use Sonnet for straightforward tasks
   - Use Opus for complex logic or nuanced requirements
3. **Monitor Progress**: Click on tickets to view agent messages and understand the workflow
4. **Review Output**: Check the `plans/` and `reviews/` directories for generated documents

## Troubleshooting

### Backend Issues
- Ensure Python 3.11+ is installed
- Check that port 8001 is available
- Verify database file is created in `backend/db/sdlc.db`

### Frontend Issues
- Ensure Node.js 18+ is installed
- Check that port 5174 is available
- Clear browser cache if UI doesn't update

### Agent Issues
- Check Claude Agent SDK is properly configured
- Ensure sufficient API credits
- Review agent messages in ticket details for errors

## Example Use Cases

1. **Feature Implementation**
   - "Add user authentication with JWT tokens"
   - "Implement a REST API for product management"

2. **Bug Fixes**
   - "Fix the memory leak in the data processing pipeline"
   - "Resolve the race condition in concurrent file writes"

3. **Refactoring**
   - "Refactor the monolithic service into microservices"
   - "Optimize database queries for better performance"

4. **Documentation**
   - "Create comprehensive API documentation"
   - "Write unit tests for the authentication module"

## Development

### Adding New Stages
1. Update database schema in `backend/db/database.py`
2. Add stage to frontend in `src/App.vue`
3. Define transition rules

### Customizing Agents
1. Modify system prompts in `system_prompts/`
2. Adjust user prompts in `user_prompts/`
3. Update orchestrator logic in `backend/modules/agent_orchestrator.py`

### Extending the UI
1. Components are in `frontend/src/components/`
2. State management in `frontend/src/stores/`
3. Styling uses scoped CSS in Vue components

## Resources

https://github.com/anish2690/vue-draggable-next
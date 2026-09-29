# Backend Quick Start Guide

## 🔑 Key Backend Nodes - Quick Reference

| Node | Purpose |
|------|---------|
| **main.py** | FastAPI endpoints and WebSocket connections |
| **config.py** | Environment variables and runtime settings |
| **logger.py** | Rich console + hourly-rotating file logs |
| **database.py** | asyncpg pool and CRUD operations |
| **websocket_manager.py** | Real-time event broadcasting to clients |
| **orchestrator_service.py** | Claude SDK execution and business logic |
| **agent_manager.py** | Agent lifecycle and 8 management tools |
| **hooks.py** | Event capture from Claude SDK |
| **orchestrator_hooks.py** | Orchestrator-specific event hooks |
| **command_agent_hooks.py** | Agent command event hooks |
| **subagent_loader.py** | Template registry discovery |
| **slash_command_parser.py** | Command discovery parser |
| **orch_database_models.py** | Pydantic type-safe models |

---

## 🎯 Find What You Need in 30 Seconds

### I'm a...

#### 👤 New Developer
**Start**: `BACKEND_DOCUMENTATION_INDEX.md` → "For New Team Members"
Then: Read the "Architecture Overview" section

**Next**: Look at the Mermaid diagrams in `backend-architecture-diagram.md`

**Goal**: Understand how modules connect

---

#### 🔧 Backend Developer
**Start**: `backend-modules-reference.md` → "Module Specification Table"

**For implementation**: Use the API reference and code examples

**Need details?** Check the specific module in `backend-structure-summary.md`

**Goal**: Implement features correctly

---

#### 📊 Data/Database Developer
**Start**: `backend-modules-reference.md` → "Database Tables Overview"

**For schema**: See the ER diagram in `backend-architecture-diagram.md`

**For operations**: Check `database.py` section in `backend-structure-summary.md`

**Goal**: Understand data model

---

#### 🌐 API Developer
**Start**: `backend-modules-reference.md` → "API Endpoints Reference"

**For flows**: See sequence diagram in `backend-architecture-diagram.md`

**For implementation**: Check `main.py` section in `backend-structure-summary.md`

**Goal**: Build reliable endpoints

---

#### 🧪 QA/Tester
**Start**: `backend-structure-summary.md` → "Testing Strategy"

**For test data**: Check "Database Schema" section

**For flows**: Review "Request/Response Flow" examples

**Goal**: Write comprehensive tests

---

#### 👨‍💼 Tech Lead/Architect
**Read**: All three main documents in order
1. `backend-structure-summary.md` (full architecture)
2. `backend-architecture-diagram.md` (visual understanding)
3. `backend-modules-reference.md` (technical details)

**Goal**: Make informed decisions

---

#### 🚀 DevOps/Infrastructure
**Start**: `backend-modules-reference.md` → "Integration Checklist"

**Configuration**: "Configuration Variables Reference" section

**Database**: PostgreSQL connection settings

**Goal**: Deploy correctly

---

## 📍 Quick Navigation

### By Topic

| Topic | Document | Section |
|-------|----------|---------|
| **Overall Architecture** | backend-structure-summary.md | Architecture Overview |
| **Module Descriptions** | backend-structure-summary.md | Core Modules Overview |
| **Visual Diagrams** | backend-architecture-diagram.md | All 11 diagrams |
| **API Endpoints** | backend-modules-reference.md | API Endpoints Reference |
| **Database Schema** | backend-modules-reference.md | Database Tables Overview |
| **Configuration** | backend-modules-reference.md | Configuration Variables |
| **Data Flows** | backend-architecture-diagram.md | Sequence & Flow Diagrams |
| **Dependencies** | backend-architecture-diagram.md | Module Dependency Tree |
| **Error Handling** | backend-structure-summary.md | Error Handling Section |
| **Testing** | backend-structure-summary.md | Testing Strategy |
| **Performance** | backend-structure-summary.md | Performance Considerations |
| **Security** | backend-modules-reference.md | Security Considerations |

---

## 🔍 Find Specific Information

### "How do I...?"

| Question | Document | Location |
|----------|----------|----------|
| Add a new API endpoint? | backend-structure-summary.md | main.py section |
| Create a new module? | backend-modules-reference.md | Best Practices |
| Connect to the database? | backend-modules-reference.md | Configuration Variables |
| Set up environment? | BACKEND_DOCUMENTATION_INDEX.md | Integration Checklist |
| Debug a WebSocket issue? | backend-architecture-diagram.md | Event Broadcasting diagram |
| Add a database table? | backend-modules-reference.md | Database Tables Overview |
| Understand module flow? | backend-architecture-diagram.md | Module Relationship Map |
| Deploy the backend? | backend-modules-reference.md | Integration Checklist |
| Write tests? | backend-structure-summary.md | Testing Strategy |
| Handle errors? | backend-structure-summary.md | Error Handling Section |

---

## 📚 Document Map

```
START HERE ↓
└─ BACKEND_DOCUMENTATION_INDEX.md (Master Index)
   ├─ Choose your role → Quick Navigation section
   │
   ├─ For Big Picture ↓
   │  └─ backend-structure-summary.md (781 lines)
   │     ├─ Architecture Overview
   │     ├─ Core Modules (1-17)
   │     ├─ Database Schema
   │     ├─ Design Patterns
   │     └─ Error Handling
   │
   ├─ For Visual Understanding ↓
   │  └─ backend-architecture-diagram.md (567 lines)
   │     ├─ 11 Mermaid Diagrams
   │     ├─ Module Relationships
   │     ├─ Data Flows
   │     ├─ Database ER Diagram
   │     └─ State Transitions
   │
   └─ For Detailed Reference ↓
      └─ backend-modules-reference.md (563 lines)
         ├─ Module Table (16×6)
         ├─ Dependency Matrix
         ├─ API Endpoints (13)
         ├─ Database Tables (6)
         ├─ Configuration
         └─ Checklists
```

---

## 🎯 Common Tasks Roadmap

### Task: Deploy Backend
1. Read: Integration Checklist in `backend-modules-reference.md`
2. Set: All environment variables (see Configuration Variables)
3. Init: PostgreSQL database with schema
4. Run: Backend with `uv run uvicorn backend.main:app`
5. Test: GET /health endpoint

### Task: Add New API Endpoint
1. Study: API Endpoints Reference in `backend-modules-reference.md`
2. Review: main.py section in `backend-structure-summary.md`
3. Check: Request/Response Flow example
4. Code: In main.py following existing patterns
5. Test: Using REST client

### Task: Create New Database Model
1. Learn: Database Schema in `backend-modules-reference.md`
2. Check: Existing models in orch_database_models.py
3. Create: Pydantic model with validators
4. Add: CRUD operations in database.py
5. Test: With real database

### Task: Debug WebSocket Issue
1. Check: Event Broadcasting Architecture diagram
2. Review: websocket_manager.py section
3. Verify: Hook events are firing (see hooks.py)
4. Trace: In logs (backend/logs/YYYY-MM-DD_HH.log)
5. Test: With WebSocket client

### Task: Understand Agent Lifecycle
1. Study: Agent Manager section in `backend-structure-summary.md`
2. Review: Agent Creation diagram in `backend-architecture-diagram.md`
3. Read: agent_manager.py module description
4. Check: Database tables (agents, agent_logs)
5. Trace: In logs during agent execution

---

## ⚡ 5-Minute Overview

### What is the Backend?
FastAPI server that orchestrates Claude SDK agents via REST + WebSocket, with PostgreSQL persistence.

### Core Components
- **FastAPI App** (main.py) - REST endpoints + WebSocket
- **Services** - OrchestratorService, AgentManager
- **Database** - asyncpg pool + CRUD operations
- **WebSocket** - Real-time event broadcasting
- **Hooks** - Event capture from Claude SDK

### Data Flow (Simple Version)
```
User → API → Service → Claude SDK → Hooks → DB + WebSocket → Frontend
```

### Key Modules
| Module | Purpose |
|--------|---------|
| main.py | HTTP routing & WebSocket |
| config.py | Environment variables |
| database.py | Database operations |
| orchestrator_service.py | Claude SDK execution |
| agent_manager.py | Agent lifecycle |
| websocket_manager.py | Real-time events |
| hooks.py | Event capture |

### API Endpoints (Quick List)
- GET `/health` - Health check
- GET `/get_orchestrator` - Metadata
- POST `/send_chat` - Process message
- GET `/get_events` - Event log
- GET `/list_agents` - Active agents
- WebSocket `/ws` - Real-time stream

### Database Tables (Quick List)
- orchestrator_agents - Singleton orchestrator
- agents - Managed agents
- agent_logs - Event log
- orchestrator_chat - Chat history
- prompts - Prompts sent
- system_logs - System events

---

## 🚨 Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| Backend won't start | Check: Integration Checklist + Environment Variables |
| API returns 500 | Check: backend/logs/YYYY-MM-DD_HH.log + Error Handling section |
| WebSocket not updating | Check: Event Broadcasting Architecture diagram |
| Database connection fails | Check: DATABASE_URL in .env |
| Agent not executing | Check: Agent Manager section |
| Costs not updating | Check: update_orchestrator_costs() in database.py |

---

## 📞 Need Help?

### If you need to understand...

| Topic | Read This |
|-------|-----------|
| How the system works overall | backend-structure-summary.md - Architecture Overview |
| How modules connect | backend-architecture-diagram.md - Module Relationship Map |
| How a specific endpoint works | backend-modules-reference.md - API Endpoints Reference |
| How data flows | backend-architecture-diagram.md - Data Flow diagrams |
| How to configure something | backend-modules-reference.md - Configuration Variables |
| How to debug | backend-structure-summary.md - Error Handling |
| How to deploy | backend-modules-reference.md - Integration Checklist |
| How to test | backend-structure-summary.md - Testing Strategy |

---

## 📊 Documentation Statistics at a Glance

```
Total Documentation Created:
  • 4 files
  • 2,395 lines
  • 63 KB
  • 11 Mermaid diagrams
  • 26+ reference tables
  • 50+ sections
```

Module Coverage: **100%** (16/16 modules documented)

---

## ✅ What's Included

✓ **Architecture Overview** - How it all works
✓ **Module Descriptions** - What each piece does
✓ **Data Flows** - How information moves
✓ **Visual Diagrams** - 11 Mermaid diagrams
✓ **API Reference** - All endpoints documented
✓ **Database Schema** - All tables explained
✓ **Configuration** - All env variables
✓ **Patterns** - 7 architectural patterns
✓ **Performance** - Optimization notes
✓ **Security** - Security best practices
✓ **Testing** - Testing strategy
✓ **Troubleshooting** - Common issues & solutions
✓ **Integration** - Deployment checklist

---

## 🎓 Learning Paths

### Path 1: Quick Learner (30 min)
1. This file (BACKEND_QUICK_START.md)
2. Architecture Overview in backend-structure-summary.md
3. Module Relationship Map in backend-architecture-diagram.md

### Path 2: Thorough Learner (2 hours)
1. All three main documentation files in order
2. All 11 Mermaid diagrams
3. Key reference tables

### Path 3: Deep Dive (4+ hours)
1. Study all documentation thoroughly
2. Review module code alongside documentation
3. Trace through complete request/response flow
4. Set up local development environment

---

## 📝 Notes

- All documentation uses plain language (not overly technical)
- Mermaid diagrams render in GitHub, GitLab, and Notion
- All code examples are production-ready patterns
- Cross-references link between documents

---

## 🎉 Ready to Get Started?

**Next Step**: Open `BACKEND_DOCUMENTATION_INDEX.md` and choose your path!

Good luck! 🚀

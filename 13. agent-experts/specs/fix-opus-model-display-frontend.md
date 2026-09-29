# Plan: Fix Frontend Display of Opus 4.5 Model for Command Level Agents

## Task Description

Command level agents (agents spawned from slash commands and agent templates) were recently updated to use the new Opus 4.5 model in their configuration files. However, the frontend still displays these agents as using "opus-4.1" instead of "opus-4.5". This plan addresses the frontend display issue by updating the model formatting logic.

## Objective

Update the frontend to correctly display "opus-4.5" for agents using the Opus model, ensuring consistency between backend configuration and frontend display.

## Problem Statement

The issue stems from a hardcoded model display mapping in the frontend's `AgentList.vue` component. The `formatModel()` function contains outdated version information:

**Current behavior:**
- Command files specify: `model: opus`
- Backend correctly reads and transmits: `"model": "opus"`
- Frontend displays: "opus-4.1" ❌ (incorrect)

**Expected behavior:**
- Command files specify: `model: opus`
- Backend correctly reads and transmits: `"model": "opus"`
- Frontend displays: "opus-4.5" ✅ (correct)

## Solution Approach

Update the `formatModel()` function in `AgentList.vue` to return "opus-4.5" instead of "opus-4.1" when the model string contains "opus". This is a simple string replacement fix that requires no backend changes or data migration.

## Relevant Files

### Files to Modify
- **apps/orchestrator_3_stream/frontend/src/components/AgentList.vue** (lines 190-199)
  - Contains the `formatModel()` function with hardcoded model version strings
  - This function formats model names for display in the agent list sidebar

### Files for Reference (No Changes Needed)
- **apps/orchestrator_3_stream/backend/modules/slash_command_parser.py**
  - Backend correctly parses and transmits model information from command files
- **.claude/commands/question-w-mermaid-diagrams.md**
  - Example command file with `model: opus` specification
- **.claude/agents/meta-agent.md**
  - Example agent template with `model: opus` specification

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update formatModel Function in AgentList.vue
- Open `apps/orchestrator_3_stream/frontend/src/components/AgentList.vue`
- Locate the `formatModel()` function (lines 190-199)
- Change the return value for opus models from `"opus-4.1"` to `"opus-4.5"`
- Verify the function still handles other model types (sonnet, haiku) correctly

**Current code:**
```typescript
const formatModel = (model: string): string => {
  if (model.includes("sonnet")) {
    return "sonnet-4.5";
  } else if (model.includes("opus")) {
    return "opus-4.1";  // ❌ INCORRECT
  } else if (model.includes("haiku")) {
    return "haiku-4.5";
  }
  return model;
};
```

**Updated code:**
```typescript
const formatModel = (model: string): string => {
  if (model.includes("sonnet")) {
    return "sonnet-4.5";
  } else if (model.includes("opus")) {
    return "opus-4.5";  // ✅ CORRECTED
  } else if (model.includes("haiku")) {
    return "haiku-4.5";
  }
  return model;
};
```

### 2. Verify Frontend TypeScript Compilation
- Ensure the TypeScript changes compile without errors
- No type changes are needed as this is a string literal change

### 3. Manual Testing in Browser
- Start the backend: `cd apps/orchestrator_3_stream && ./start_be.sh`
- Start the frontend: `cd apps/orchestrator_3_stream && ./start_fe.sh`
- Open the application in a browser
- Create an agent using a command with `model: opus` (e.g., run `/question-w-mermaid-diagrams`)
- Verify the agent list sidebar displays "opus-4.5" for the new agent
- Verify existing agents with other models (sonnet, haiku) still display correctly

## Acceptance Criteria

- ✅ The `formatModel()` function returns "opus-4.5" for any model string containing "opus"
- ✅ Frontend compiles without TypeScript errors
- ✅ Agents spawned from opus-model commands display "opus-4.5" in the agent list sidebar
- ✅ Existing model formatting for sonnet and haiku remains unchanged
- ✅ No backend changes required - this is purely a frontend display fix

## Validation Commands

Execute these commands to validate the task is complete:

1. **Check TypeScript compilation:**
   ```bash
   cd apps/orchestrator_3_stream/frontend
   npm run build
   ```
   Expected: Build completes successfully with no errors

2. **Verify the code change:**
   ```bash
   grep -A 5 "formatModel.*model.*string" apps/orchestrator_3_stream/frontend/src/components/AgentList.vue
   ```
   Expected: Should show "opus-4.5" in the function, not "opus-4.1"

3. **Manual browser test:**
   - Start backend and frontend
   - Run a command with opus model (e.g., `/question-w-mermaid-diagrams test question`)
   - Check agent list sidebar displays "opus-4.5"

## Notes

### Why Just "opus" in Command Files?
The command files use simplified model identifiers like `model: opus`, `model: opus`, or `model: haiku`. The Claude SDK maps these to the full model identifiers (e.g., `claude-opus-4-20250514`). The frontend's `formatModel()` function provides human-readable versions for the UI.

### No Backend Changes Required
The backend correctly reads and transmits the model field from command/agent files. This issue is purely a frontend display problem in the `AgentList.vue` component.

### Single Point of Change
The `formatModel()` function is the only place in the frontend that formats model names for display, so this single change fixes the issue across the entire application.

### Future Considerations
Consider creating a centralized model version constant file (e.g., `modelVersions.ts`) if model versions change frequently, rather than hardcoding them in display functions.

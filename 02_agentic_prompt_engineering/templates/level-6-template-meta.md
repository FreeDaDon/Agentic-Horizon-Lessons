# Level 6 — Template Meta Prompt

> A prompt that **creates prompts** in your house format. The Specified Format section is the template, and the agent fills in its `<placeholders>`. This is the level where your prompt-writing speed goes up the most.

```md
---
allowed-tools: Write, Edit, WebFetch, Task
description: Create a new reusable prompt in the house format
argument-hint: [high-level description of the prompt to create]
model: opus
---

# MetaPrompt

Based on the `HIGH_LEVEL_PROMPT`, follow the `Workflow` to create a new prompt in the `Specified Format`. Before you start, fetch everything in `Documentation`.

## Variables

HIGH_LEVEL_PROMPT: $ARGUMENTS
OUTPUT_DIR: .claude/commands/

## Workflow

- Save the new prompt to `OUTPUT_DIR/<name_of_prompt>.md`; the name must follow from `HIGH_LEVEL_PROMPT`.
- VERY IMPORTANT: The prompt must be in the `Specified Format`. Do not create sections or headers that are not in it.
- Replace every `<placeholder>` with content derived from `HIGH_LEVEL_PROMPT`.
- Use one `Task` per documentation item to fetch docs in parallel.
- If no variables are needed, omit the Variables section. Put dynamic variables (`$1`, `$2`) before static ones.
- Ultra think: you are writing a prompt for other agents. Optimize for clarity and determinism.

## Documentation

- Slash commands: https://docs.claude.com/en/docs/claude-code/slash-commands
- Settings & tools: https://docs.claude.com/en/docs/claude-code/settings

## Specified Format

    ---
    allowed-tools: <comma-separated tools>
    description: <description used to identify this prompt>
    argument-hint: [<first dynamic variable>] [<second dynamic variable>]
    model: sonnet
    ---

    # <name_of_prompt>

    <purpose: what the prompt does; reference the Instructions section>

    ## Variables
    <NAME_OF_DYNAMIC_VARIABLE>: $1
    <NAME_OF_STATIC_VARIABLE>: <static value>

    ## Instructions
    <bullet list of rules>

    ## Workflow
    <numbered step-by-step tasks>

    ## Report
    <how to respond to the user>
```

## Plan-template variant

The same idea applied to specs: a planner prompt with a `## Plan Format` block (Metadata, Objective, Problem Statement, Solution Approach, Relevant Files, Implementation Phases, Step-by-Step Tasks, Testing Strategy, Acceptance Criteria, Validation Commands, Notes). See `10. agentic-prompt-engineering/.claude/commands/plan_vite_vue.md`.

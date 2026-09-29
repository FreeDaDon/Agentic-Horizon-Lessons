# Agentic Prompt Engineering

> The prompt is THE fundamental unit of engineering.
>
> Invest in your prompts for the trifecta to achieve asymmetric engineering in the age of agents.

## The 7 Levels of Agentic Prompt Formats

### Level 1

High Level Prompt

> Reusable, adhoc, static prompt.

- Sections
  - Title
  - High Level Prompt (required)
  - Purpose

- Example Prompts
  - .claude/commands/all_tools.md
  - .claude/commands/start.md

### Level 2

Workflow Prompt

> Sequential workflow prompt with input, work, and output.

- Sections
  - Metadata
  - Workflow (required)
  - Instructions (secondary)
  - Variables (secondary)
  - Report (secondary)
  - Relevant Files
  - Codebase Structure
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/prime.md`
  - `.claude/commands/build.md`
  - `.claude/commands/quick-plan.md`
  - `.claude/commands/prime_tier_list.md`

### Level 3

Control Flow Prompt

> A prompt that runs conditions or/and loops in the workflow.

- Sections
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/build.md`
  - `.claude/commands/create_image.md`
  - `.claude/commands/edit_image.md`

### Level 4

Delegate Prompt

> A prompt that delegates the work to other agents (primary or subagents).

- Sections
  - Variables w/agent config (model, count, tools, etc)
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/parallel_subagents.md`
  - `.claude/commands/load_ai_docs.md`
  - `.claude/commands/background.md`

### Level 5

Higher Order Prompt

> Accept another reusable prompt (file) as input. Provides consistent structure so the lower level prompt can be changed.

- Sections
  - Variables w/prompt file variable (required)
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/build.md`
  - `.claude/commands/load_bundle.md`

### Level 6

Template Metaprompt

> A prompt that is used to create a new prompt in a specific dynamic format.

- Sections
  - Template (required)
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/t_metaprompt_workflow.md`
  - `.claude/commands/plan_vite_vue.md`

### Level 7

Self Improving Prompt

> A prompt that is updated by itself or another prompt/agent with new information.

- Sections
  - Expertise
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/experts/cc_hook_expert/cc_hook_expert_plan.md`


## Agentic Prompt Sections

> Ordered list of common and rare agentic prompt sections you can use to build a new prompt.

- `Metadata`
- `# Title`
- `## Purpose`
- `## Variables`
- `## Instructions`
- `## Relevant Files`
- `## Codebase Structure`
- `## Workflow`
- `## Expertise`
- `## Template`
- `## Examples`
- `## Report`

### Metadata

Provides configuration and metadata about the prompt using YAML frontmatter. Includes `allowed-tools` to specify which tools the prompt can use, `description` for prompt identification, `argument-hint` to guide user input, and optionally `model` to set the AI model (sonnet/opus).

### Title

The main heading that names the prompt, typically using a clear, action-oriented name. Should immediately communicate what the prompt does.

### Purpose

Describes what the prompt accomplishes at a high level and its primary use case. Sets context for the user about when and why to use this prompt. Often references key sections like Workflow or Instructions to guide the reader.

### Variables

Defines both dynamic variables (using `$1`, `$2`, `$ARGUMENTS`) that accept user input and static variables with fixed values. You can reference these variables throughout the prompt using `{{variable_name}}` syntax. For higher-order prompts, this is where prompt file paths are specified.

### Instructions

Provides specific guidelines, rules, and constraints for executing the prompt. Written as bullet points detailing important behaviors, edge cases to handle, and critical requirements. Acts as the guardrails ensuring consistent and correct execution.

### Relevant Files

Lists specific files or file patterns that the prompt needs to read, analyze, or modify. Helps establish context and ensures the prompt has access to necessary codebase resources. Particularly useful for prompts that work with existing project structures.

### Codebase Structure

Documents the expected directory layout and file organization relevant to the prompt's operation. Shows where files should be created, where to find existing resources, and how components relate to each other. Essential for prompts that generate or modify project structures.

### Workflow

The core execution steps presented as a numbered list detailing the sequence of operations. Each step should be clear and actionable, often including conditional logic for different scenarios. This is where control flow (loops, conditions) and task delegation to other agents occurs in higher-level prompts.

### Expertise

Contains accumulated knowledge, best practices, and patterns specific to the prompt's domain. Acts as embedded documentation that evolves over time, making the prompt "self-improving" (Level 7). Includes architectural knowledge, discovered patterns, standards, and detailed technical context. This prompt can be self improving but works bets when a separate prompt is dedicated to updating the expertise.

### Template

Provides reusable patterns or boilerplate structures that can be adapted for similar use cases. Often includes code snippets, configuration templates, or structural patterns. Helps users understand how to create variations of the prompt or apply its patterns elsewhere.

### Examples

Demonstrates concrete usage scenarios with actual command invocations and expected outcomes. Shows different parameter combinations and use cases to help users understand the prompt's capabilities. Essential for complex prompts where usage patterns aren't immediately obvious.

### Report

Defines how results should be presented back to the user after execution. Specifies the format, structure, and level of detail for output. Can include markdown templates, required sections, metrics to report, or summary formats that best communicate the work completed.

## System Prompts vs User Prompts

> The most important difference is scope and persistence. 
> 
> System prompts set the rules for all conversations. 
> 
> User prompts ask for specific tasks.

### System Prompts

System prompts tell the AI who it is and how to behave in every conversation. 

They're like the AI's personality and rule book combined.

**What they do:**
- Set the AI's role ("You are a helpful coding assistant")
- Define what the AI can and can't do
- Establish the tone and style for all responses
- Create rules that apply to every single interaction

**How to write them:**
- Be very clear - you can't fix confusion later
- Think about edge cases - what could go wrong?
- Test thoroughly - mistakes affect everything
- Keep them focused - too many rules create conflicts
- Use simple, exact language

**Example:**
```
You are a Python tutor. Always explain code step by step. 
Never write code longer than 10 lines without explaining it. 
If a user asks about other languages, politely redirect to Python.
```

### User Prompts

User prompts ask the AI to do specific tasks. They work within the rules set by the system prompt.

**What they do:**
- Request specific actions or information
- Provide context for the current task
- Give examples of what you want
- Can be refined based on responses

**How to write them:**
- Be clear about what you want right now
- Include relevant details and context
- Show examples if helpful
- You can ask follow-up questions to improve results

**Example:**
```
Write a function that reverses a string. Use a for loop and explain each line.
```

### Key Differences

| System Prompt                     | User Prompt                    |
| --------------------------------- | ------------------------------ |
| Sets rules for ALL conversations  | Asks for ONE specific thing    |
| Can't be changed mid-conversation | Can be refined with follow-ups |
| Needs to handle many scenarios    | Focuses on current task only   |
| Mistakes affect everything        | Mistakes affect one response   |
| Written once, used many times     | Written fresh each time        |

### Why This Matters

A bad system prompt is like bad instructions for a whole job - everything goes wrong. A bad user prompt is like unclear directions for one task - you can just ask again better.

System prompts need more testing because they affect everything. User prompts can be fixed on the fly. That's why engineers spend more time perfecting system prompts - they're the foundation everything else builds on.

### Which Sections Work Best for System Prompts

Not all prompt sections make sense for system prompts. Here's what to use and what to skip:

**Essential Sections:**

**Purpose** - Define the AI's core identity and role
- "You are a senior Python developer who writes secure, well-tested code"
- "You are a patient tutor who breaks down complex topics into simple steps"

**Instructions** - Set the behavioral rules that apply to every interaction
- How to use tools ("Always read files before editing them")
- Safety boundaries ("Never delete files without explicit confirmation")
- Output preferences ("Keep responses concise and actionable")
- Error handling ("If unclear, ask for clarification rather than guess")

**Examples** - Show expected behavior patterns (not task examples)
- How to format responses
- How to handle ambiguous requests
- What good vs bad output looks like

**Workflow** - Usually too specific. System prompts set general behavior, not step-by-step tasks. Exception: You might define a general approach like "Always understand before implementing."

**Sections to Avoid:**

**Variables** - System prompts don't take input parameters. They're static rules.


**Report/Expertise/Templates** - Too task-specific for system prompts.

**Metadata/Relevant Files/Codebase Structure** - These are for specific prompt files, not system-wide behavior.

### Common System Prompt Patterns

**Tool Usage Instructions:**
```
When working with files:
1. Always use Read before Edit
2. Create parent directories before writing files
3. Never use shell commands for file operations - use the provided tools
```

**Behavioral Boundaries:**
```
If asked to do something harmful or unethical, politely decline and explain why.
Never execute commands that could damage the system.
Always confirm before making destructive changes.
```

**Output Formatting:**
```
Structure responses as:
- Brief summary of what you'll do
- Execute the task
- Confirm completion with specific details
Keep explanations under 3 sentences unless asked for more detail.
```

**The Key Insight:** System prompts should focus on WHO the AI is and HOW it should behave across all situations. Skip anything task-specific - that belongs in user prompts.


## Claude Code Bash Alias

```bash
alias cld="claude"
alias cldp="claude -p"
alias cldo="claude --model opus"
alias clds="claude --model sonnet"
alias cldys="claude --dangerously-skip-permissions --model sonnet"
alias cldy="claude --dangerously-skip-permissions --model sonnet"
alias cldyo="claude --dangerously-skip-permissions --model opus"
alias lfg="claude --dangerously-skip-permissions --model opus"
alias cldpy="claude -p --dangerously-skip-permissions"
alias cldpyo="claude -p --dangerously-skip-permissions --model opus"
alias cldr="claude --resume"
```
# Elite Context Engineering

> A focused engineer is a performant engineer AND a focused agent is a performant agent.


## Purpose

- Master the R&D framework to optimize your context windows for high performance agentic coding
- Prevent context bloat and context rot through systematic reduction
- Delegate effectively to preserve your primary agent's focus
- Manage your context window so your model and prompt have the maximum effective context

## Setup

1. Copy `.env.sample` to `.env`
2. Add your API keys:
   - `ANTHROPIC_API_KEY` - For Claude API access
   - `ELEVENLABS_API_KEY` - For TTS features
   - `OPENAI_API_KEY` - For OpenAI integrations

## The R&D Framework

*A focused engineer is a performant engineer.*  
**A focused agent is a performant agent.**

Context engineering is the name of the game for high-value engineering in the age of agents. So, how good are your context engineering skills?

There are 3 levels of context engineering techniques and a fourth, **hidden level**, if you're on the bleeding edge pushing into 'Agentic Engineering'.

### Why Context Engineering Matters

The context window is the PRECIOUS and DELICATE resource that determines your agent's performance. There's a sweet spot - a range of context where your agent performs at maximum capability for the task at hand.

There are only two ways to manage your context window effectively:

**R and D - Reduce and Delegate**

- **Reduce**: Remove junk context, minimize token usage, focus on what matters
- **Delegate**: Offload work to sub-agents, separate agents, or specialized systems

The real skill in context engineering is **search and destroy** - finding the right context agentically while removing or delegating everything else.

## Levels

- Beginner
- Intermediate
- Advanced
- Agentic

### Technique #1: Measure to Manage

> Level: Beginner | **Framework: Foundation for R&D**

> What gets measured gets managed. Your agent's context window is a precious, limited resource.

The context window is the single most important leverage point for effective agentic coding. You must measure it to improve it.

Two primary tools:
- **`/context` Command**: Shows exactly how much context your agent processes EVERY prompt execution
- **Token Counters**: Extensions that give real-time estimates BEFORE adding files to context

This foundational technique enables everything else. Without actively monitoring your agent's context state, you're just "vibe coding" - limited to low-hanging fruit in a saturated space.

To push further, learn to see from your agent's perspective by constantly measuring and managing the context window.

### Technique #2: Avoid MCP Servers

> Level: Beginner | **Framework: Reduce**

> MCP Servers consume your context window on agent startup.
>
> Often times we don't need the MCP Servers.
>
> So we should avoid MCP Servers when possible to preserve the context window to prevent context bloat and context rot.

There are 3 scopes for MCP servers:

- Local scope: `claude mcp {add|remove|list|get|add-json|...}` run `claude mcp --help` for all options
- User Scope: `claude mcp ... --scope user ...`
- Project scope: `path/to/repo/.mcp.json`

Use `claude mcp list` to list all MCP servers.

Use `claude --mcp-config .mcp.json --strict-mcp-config` to only include MCP servers that are defined in the `.mcp.json` file.

Avoid user and local scope global MCP servers `~/.claude/.mcp.json`. Why? Because you likely don't ALWAYS need them.

Instead use no mcp servers to start, then use `claude --mcp-config <some specific mcp.json file>`.

If you do still want global MCP servers (user or local scope) and you want to exclusively use a specific MCP server to overwrite the global MCP servers for a single Claude Code instance, you can use `claude --mcp-config <some specific mcp.json file> --strict-mcp-config`. This will override the global MCP servers for that single Claude Code instance and only use the MCP servers defined in the specific mcp.json file.

### Technique #3: MORE Prime Less CLAUDE.md

> Level: Beginner | **Framework: Reduce**

> Context priming over static memory files. Dynamic, controllable setup beats always-on context.

The problem with CLAUDE.md (or any auto-loading memory file):
- It's always loaded into your agent's context window
- Engineering work changes constantly, but the file doesn't
- Grows bloated with context not relevant to every task
- Risk of contradictory information as teams add content

**Solution: Context Priming**

Instead of static files, use dedicated custom slash commands to prime your agent for specific task types:
- `/prime` - Basic codebase understanding
- `/prime_bug` - Bug fixing context
- `/prime_feature` - Feature development setup
- `/prime_testing` - Testing-specific context

Stack commands for specialized workflows: `/prime_cc` executes base prime then loads all .claude files for Claude Code-specific work.

Your CLAUDE.md should only contain absolute universals needed 100% of the time. Everything else: prime dynamically.

### Technique #4: Control Output Tokens

> Level: Intermediate | **Framework: Reduce**

> Output tokens cost 3-5x more than input tokens. Control them with output styles.

Output tokens are the most expensive part of your agent and get added back to context, creating compound costs.

Claude Code's output styles let you limit and guide token generation:
- `concise-done.md` - Minimal responses, just "Done."
- `concise-ultra.md` - Ultra-brief responses
- `verbose-yaml-structured.md` - Structured but detailed

Example impact: Simple "What does this codebase do?" prompt
- Default output: ~500 tokens added to context
- Concise style: ~50 tokens added to context

Over tens or hundreds of prompts, this difference compounds massively. A focused agent with controlled output is a performant agent.

### Technique #5: Use Sub Agents - PROPERLY

> Level: Intermediate | **Framework: Delegate**  

> Sub agents create "partially forked context windows" - their system prompts don't consume your primary agent's context.

When you use sub agents correctly:
- System prompts stay isolated from primary context
- Sub agents respond to your primary agent, not you
- Primary agent prompts sub agents based on your instructions

Best for tasks that can operate in isolation with minimal context from primary agent. Example: `/load_ai_docs` delegates documentation fetching to parallel sub agents, protecting primary context.

Key: Write sub agents to return concise, reduced reports to your primary agent. This is delegation at work - the D in the R&D (Reduce & Delegate) framework.

### Technique #6: Use the Architect Editor Multi-Agent Pattern

> Level: Intermediate | **Framework: R&D (Reduce via Delegation)**

> Separate planning from implementation. A focused agent is a performant agent.

Two agents working side by side:
1. **Architect/Planner**: Gathers context, explores options, creates spec files
2. **Editor/Builder**: Reads spec, implements with surgical precision

The planner wastes tokens finding the right context - that's its job. The implementor gets a crystal-clear context window for error-free edits.

Example workflow:
```bash
/quick-plan "create wrapper system for claude code typescript sdk..."
# Planner explores, creates detailed spec
# Fresh builder agent implements from spec
```

This ensures your implementor has maximum focus for perfect execution.

### Technique #7: Avoid compact - reset and prime

> Level: Advanced | **Framework: Reduce**

> `/compact` is a bandaid. Know your context exactly instead of guessing.

The problem with `/compact`:
- You don't know exactly what's retained
- Always loses key information in compression
- Puts agent in decent but unknown state

**Better approach**: Full reset + context prime
- `/clear` to reset completely  
- `/prime` or `/prime_[task]` to reload exact context
- You know precisely what's in the window

This prepares you for out-loop agentic coding where no single agent should exceed 200k tokens. If it does, chop up the task.

### Technique #8: Use Context Bundles

> Level: Advanced | **Framework: Reduce**

> Track and reuse context across sessions with hooks that capture file operations.

Context bundles automatically capture:
- Files read and written per session
- Stored in `agents/context_bundles/<session_id>_<datetime>.jsonl`
- Quickly reload previous session's exact context

Commands:
- `/status` - Get current session ID
- `/load_bundle <bundle_file>` - Reload previous context
- `/prime_bundle` - Custom prime with bundle loading

This technique enables instant context restoration for fresh agents, building on the reset-and-prime pattern. Perfect for long development sessions.

### Technique #9: Use one agent for one purpose

> Level: Advanced | **Framework: R&D**

> A focused agent is a performant agent. Ship one thing at a time.

This summarizes all previous techniques:
- Forces you to define: "What's this agent's single purpose?"
- Plan the pipeline of agents for complex work
- Each agent has maximum focus for its specific task

Workflow:
1. Plan work completely separate from technology
2. Design agent pipeline (AI Developer Workflow)
3. Execute with single-purpose agents

This is the foundation for scaling to AI Developer Workflows - the highest leverage in agentic coding.

### Technique #10: System Prompt

> Level: Agentic | **Framework: Reduce**

> Gain fine-tuned control with `--append-system-prompt` and the SDK's `customSystemPrompt`.

Control Claude Code's behavior at the deepest level:
- `--append-system-prompt` - Add to existing system prompt
- `customSystemPrompt` (SDK) - Complete overwrite (dangerous!)

Example: Force incremental file reading:
```bash
claude --append-system-prompt "ALWAYS read files in 100-line increments..."
```

This trades time for context - agent reads chunks of 100 instead of entire files.

Only use when nothing else works or building custom out-loop agents. The Claude Code team has carefully crafted the default prompt.

### Technique #11: Primary Multi-Agent Delegation

> Level: Agentic | **Framework: Delegate**

> Orchestrate multiple primary agents. Maximum delegation with complete context isolation.

Unlike sub agents, primary agents are completely independent:
- Full Claude Code instances with separate context
- Can use different models, settings, prompts
- Report back via files or structured outputs

Lightweight implementation: `/background` command
```bash
/background "/quick-plan ..." sonnet report.md
```

Agents orchestrating agents - compute managing compute. Perfect for parallel work streams.

Be careful: Runs directly on your API keys. Must be managed properly.

### Technique #12: Agent Experts

> Level: Agentic | **Framework: R&D**

> Self-improving specialized agents with plan-build-improve cycles.

Agent Experts are specialized agent sets for codebase areas:
- **Plan**: Investigate and create specifications
- **Build**: Execute from specifications  
- **Improve**: Update expert knowledge based on work done

Example workflow:
```bash
/experts:cc_hook_expert:cc_hook_expert_plan "implement session logging..."
/experts:cc_hook_expert:cc_hook_expert_build <path_to_plan>
/experts:cc_hook_expert:cc_hook_expert_improve
```

The improve step makes experts self-documenting - they update their own knowledge for future runs.

This pattern scales engineering by encoding expertise in reusable, self-improving agent pipelines.

---

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
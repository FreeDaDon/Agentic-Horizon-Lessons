# QA Agent - Codebase Question & Answer System

A specialized REPL agent for answering questions about codebases using parallel search capabilities and the Claude Agent SDK.

## Features

- 🔍 **Parallel Search**: Deploys multiple Task subagents simultaneously for comprehensive codebase analysis
- 💬 **Interactive REPL**: Continuous conversation with session memory
- 🎨 **Rich Terminal UI**: Beautiful panels for all message types (text, tools, thinking, results)
- 📝 **Custom Slash Command**: `/qa_agent` automatically wraps all queries for focused Q&A
- 🚫 **Controlled Tool Access**: Only allows codebase analysis tools (no editing)
- 🔌 **MCP Integration**: Optional Firecrawl support for documentation scraping
- 📊 **Session Statistics**: Track duration, costs, and API usage
- 🔒 **Inline Hook Security**: Blocks .env files for ALL agents including subagents

## Installation

```bash
cd apps/custom_5_qa_agent
uv sync
```

## Usage

### Basic Usage

```bash
uv run python qa_agent.py
```

### REPL Commands

Once in the REPL:

- **Ask a question**: Just type your question or use `/qa_agent <question>`
- `/help` - Show available commands
- `/stats` - Display session statistics
- `/clear` - Clear conversation history
- `/exit` or `quit` - Exit the agent

### Example Queries

```
QA[0]> How does the social hype agent handle notifications?

QA[1]> /qa_agent What custom tools are implemented in the calc agent?

QA[2]> Show me all the uses of ClaudeSDKClient in the codebase

QA[3]> What's the architecture of the tri-copy-writer app?
```

## Architecture

### System Prompt

The QA Agent uses a specialized system prompt that:
- Instructs parallel deployment of Task subagents for search
- Redirects non-codebase questions to WebSearch
- Provides comprehensive codebase structure context
- Defines clear response formatting rules

### Allowed Tools

- **Task**: Deploy parallel search subagents
- **Read**: Examine specific files
- **WebSearch**: For non-codebase queries
- **WebFetch**: Documentation fetching
- **Bash**: Git history and file statistics
- **Firecrawl** (optional): Documentation scraping

### Disallowed Tools

All editing tools are explicitly blocked:
- Edit, MultiEdit, Write
- NotebookEdit
- TodoWrite
- File manipulation tools

## Codebase Structure

```
apps/custom_5_qa_agent/
├── README.md                       # Documentation and usage guide
├── qa_agent.py                     # Main QA Agent REPL implementation
├── prompts/
│   └── QA_AGENT_SYSTEM_PROMPT.md  # System prompt for agent behavior
├── test_inline_hooks.py           # Security hook testing suite
├── pyproject.toml                 # Project dependencies and configuration
└── uv.lock                        # Locked dependencies for reproducibility
```

### Key Files

- **`qa_agent.py`**: Core implementation with REPL, hooks, and display functions
- **`QA_AGENT_SYSTEM_PROMPT.md`**: Defines agent's codebase analysis behavior
- **`test_inline_hooks.py`**: Validates security hook functionality
- **`pyproject.toml`**: Specifies dependencies (claude-agent-sdk, rich)

## Security Features

### Inline Hook-Based Security

The QA Agent implements comprehensive security using inline hooks that monitor ALL tool calls, including those from subagents:

#### Hook Functions

1. **`block_env_files`** - Blocks access to .env files
   - Intercepts all Read, Grep and Bash tool calls
   - Denies any file path, Grep path/glob or Bash command containing `.env`
   - Works for both main agent and subagents
   - Returns proper denial response to Claude

2. **`log_tool_usage`** - Audits tool usage
   - Logs Read, Write, Edit, and Bash operations
   - Timestamps all security-relevant actions
   - Provides audit trail for security monitoring

#### Blocked Operations
- **`.env` files**: All environment files are completely blocked
- **Sensitive files**: Warns about files containing:
  - credentials, secrets, passwords
  - tokens, API keys, private keys
  - `.pem`, `.key`, `.crt` files

#### Key Advantage
✅ **Full Coverage**: Unlike `can_use_tool` which only works for the main agent, hooks intercept ALL tool calls including those from Task subagents, providing comprehensive security coverage.

#### Implementation
```python
hooks = {
    'PreToolUse': [
        HookMatcher(matcher='Read|Grep|Bash', hooks=[block_env_files]),
        HookMatcher(hooks=[log_tool_usage])  # All tools
    ],
    'PostToolUse': [
        HookMatcher(hooks=[log_tool_usage])
    ]
}
```

#### Security Logging
- 🔒 Red alerts for blocked `.env` access attempts
- ⚠️ Yellow warnings for potentially sensitive file access
- 🕐 Timestamped audit logs for tool usage

#### Testing Security
Run the inline hooks test suite:
```bash
uv run python test_inline_hooks.py
# or
uv run --with pytest pytest test_inline_hooks.py
```

This tests the hook functions directly and verifies blocking behavior.

## Message Type Handling

The agent displays each message type with rich formatting:

- **TextBlock**: Rendered as markdown with syntax highlighting
- **ToolUseBlock**: Yellow panels showing tool invocation details
- **ToolResultBlock**: Green/red panels for success/error results
- **ThinkingBlock**: Subtle gray panels for reasoning display
- **SystemMessage**: Dim panels for system notifications
- **ResultMessage**: Session statistics and cost tracking

## Configuration

### MCP Server (Optional)

To enable Firecrawl integration, ensure `.mcp.json.firecrawl_4k` exists with your API key:

```json
{
  "mcpServers": {
    "firecrawl-mcp": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Customization

- Modify `prompts/QA_AGENT_SYSTEM_PROMPT.md` to adjust agent behavior
- Edit `.claude/commands/qa_agent.md` to change the slash command
- Adjust allowed/disallowed tools in `qa_agent.py`

## Development

### Key Components

1. **QAAgentREPL class**: Main REPL implementation
   - Session management
   - Client initialization
   - Query processing
   - Display formatting

2. **Display Functions**: Rich terminal output
   - `display_tool_use()`: Format tool invocations
   - `display_tool_result()`: Show tool results
   - `display_thinking()`: Render thinking blocks
   - `display_text()`: Markdown rendering
   - `display_session_stats()`: Statistics table

3. **Configuration Loading**:
   - System prompt from `prompts/`
   - MCP config from `.mcp.json.firecrawl_4k`
   - Tool access control lists

## Learning Objectives

This agent demonstrates:

- **Level 2 Complexity**: Multi-tool orchestration with parallel execution
- **REPL Design**: Interactive conversation with session continuity
- **Rich UI**: Comprehensive message type handling with beautiful formatting
- **Tool Control**: Explicit allow/disallow lists for fine-grained control
- **Custom Commands**: Integration with Claude Code slash commands
- **MCP Integration**: External tool server configuration
- **Security Implementation**: Custom permission handlers with `can_use_tool` parameter
  - `PermissionResultAllow` for approved operations
  - `PermissionResultDeny` for blocked operations
  - `ToolPermissionContext` for context-aware decisions
# Building Specialized Agents
> Better agents, More agents, then... **Custom Agents**
>
> After you master Context Engineering, and Agentic Prompt Engineering, it's time to build your own specialized, domain specific, custom agents.

## Custom Agent Capabilities

### Pong Agent: 

- **Purpose:** Learn basic Claude Agent SDK fundamentals
- **Interface:** CLI Script
- **Location:** apps/custom_1_pong_agent
- **Capabilities:**
  - Basic Claude Agent SDK setup
  - Simple query/response pattern
  - Complete System Prompt override
  - Cost tracking
  - Model selection
- **Run:**
    ```bash
    uv run python apps/custom_1_pong_agent/pong_agent.py
    ```

### Echo Agent:

- **Purpose:** Custom tool creation with parameters
- **Interface:** CLI Script
- **Location:** apps/custom_2_echo_agent
- **Capabilities:**
  - ClaudeSDKClient for custom tools
    - echo_tool(message: str, repeat: int, transform: str)
  - Tool use control with `allowed_tools`
- **Run:**
    ```bash
    uv run python apps/custom_2_echo_agent/echo_agent.py
    ```

### Calculator Agent:

- **Purpose:** Interactive REPL with session continuity and multiple custom tools
- **Interface:** Interactive REPL
- **Location:** apps/custom_3_calc_agent
- **Capabilities:**
  - Interactive REPL with conversation memory with `resume` parameter
  - Multiple custom tools working together:
    - custom_math_evaluator(expression: str, precision: int)
    - custom_unit_converter(value: float, from_unit: str, to_unit: str)
  - Tool control with `allowed_tools` and `disallowed_tools`
- **Run:**
    ```bash
    uv run python apps/custom_3_calc_agent/calc_agent.py
    ```

### Social Hype Agent:

- **Purpose:** Real-time social media monitoring with AI-powered content analysis
- **Interface:** CLI w/args
- **Location:** apps/custom_4_social_hype
- **Capabilities:**
  - Real-time Bluesky WebSocket firehose monitoring
  - Keyword-based content filtering (configurable search terms)
  - Claude Agent SDK integration for content summarization
  - Sentiment analysis (positive, negative, neutral)
- **Run:**
    ```bash
    # Monitor single keyword
    uv run python apps/custom_4_social_hype/social_hype_agent.py coding python javascript rust -n "notify me when there are any mentions of rust"

    uv run python social_hype_agent.py "openai" "chatgpt" "chat-gpt" "gemini" "claude" "claude code" "anthropic" -n "Any mention of claude or anthropic outages or performance issues"

    uv run python social_hype_agent.py "openai" "chatgpt" "chat-gpt" "gemini" "claude" "claude code" "anthropic" -n "Any mention of new LLM models or tech releases from openai, gemini, or anthropic"

    ```

### QA Agent:

- **Purpose:** Specialized REPL for codebase question answering with parallel search
- **Interface:** Interactive REPL
- **Location:** apps/custom_5_qa_agent
- **Capabilities:**
  - Parallel Task deployment for comprehensive codebase search
  - Interactive REPL with conversation continuity via `resume` parameter
  - Custom slash command integration (`/qa_agent`)
  - Rich terminal UI with panels for all message types
  - Controlled tool access (read-only, no editing)
  - Optional MCP server integration (Firecrawl)
  - Session statistics and cost tracking
- **Run:**
    ```bash
    uv run python apps/custom_5_qa_agent/qa_agent.py
    ```


### Tri-Copy-Writer Agent:

- **Purpose:** Professional copywriting with multiple variations and file context support
- **Interface:** Web application (Vue.js frontend + FastAPI backend with CLI params)
- **Location:** apps/custom_6_tri_copy_writer
- **Capabilities:**
  - Multiple copy variations (1-10 configurable via CLI `-v` flag)
  - Drag & drop file context support (text/markdown files)
  - Professional copywriting interface with copy-to-clipboard
  - Structured JSON responses: `{primary_response, multi_version_copy_responses}`
  - Advanced web UI with toast notifications and file management
  - CLI parameter integration for dynamic configuration
  - Real-time cost tracking and session metadata
- **Run:**
    ```bash
    # Start backend with default 3 variations (in one terminal)
    cd apps/custom_6_tri_copy_writer/backend
    uv sync && uv run python main.py

    # Or start with custom number of variations
    uv run python main.py -v 5

    # Start frontend (in another terminal)
    cd apps/custom_6_tri_copy_writer/frontend
    npm install && npm run dev

    # Open browser to http://127.0.0.1:5173
    ```

### Micro SDLC Agent:

- **Purpose:** Orchestrate engineering work through Plan, Build, and Review stages with specialized agents
- **Interface:** Web application (Vue.js kanban board + FastAPI backend)
- **Location:** apps/custom_7_micro_sdlc_agent
- **Capabilities:**
  - **Three Specialized Agents:**
    - Planner Agent - Creates detailed implementation plans from requirements
    - Builder Agent - Executes plans and implements solutions
    - Reviewer Agent - Reviews implementations against plans
  - **Kanban Board Interface:**
    - 7 workflow stages (Idle → Plan → Build → Review → Shipped/Errored → Archived)
    - Drag-and-drop with stage transition rules
    - Real-time progress monitoring via WebSocket
  - **Agent Orchestration:**
    - Automated workflow progression
    - Agent message tracking with emojis
    - Tool call statistics per phase
    - Session ID tracking for each agent
  - SQLite database for persistent ticket management
  - Support for Sonnet (faster) and Opus (smarter) models
  - Generated plans saved to `plans/` directory
  - Generated reviews saved to `reviews/` directory
- **Run:**
    ```bash
    # Start backend (in one terminal)
    cd apps/custom_7_micro_sdlc_agent/backend
    uv sync && uv run python main.py

    # Start frontend (in another terminal)
    cd apps/custom_7_micro_sdlc_agent/frontend
    npm install && npm run dev

    # Open browser to http://127.0.0.1:5173
    ```

### Ultra Stream Agent:

- **Purpose:** Dual-agent system for real-time log stream processing and intelligent inspection
- **Interface:** Web application (Vue.js dual-panel frontend + FastAPI backend)
- **Location:** apps/custom_8_ultra_stream_agent
- **Capabilities:**
  - **Stream Agent** - Continuous JSONL processing:
    - Reads and summarizes logs in small batches (3-5 lines)
    - Automatic severity classification (low/medium/high)
    - High-severity alert generation with user context
    - Context window management for infinite operation
  - **Inspector Agent** - Intelligent log analysis:
    - Natural language queries about processed logs
    - User-specific log investigation
    - Pattern detection and anomaly identification
    - Team notifications (Engineering & Support)
  - Dual-panel Vue.js interface with real-time WebSocket updates
  - SQLite database for log persistence
  - Session continuity across agent restarts
- **Run:**
    ```bash
    # Generate sample data (optional, for testing)
    cd apps/custom_8_ultra_stream_agent
    uv sync && uv run python generate_sample_data.py

    # Start backend (in one terminal)
    uv run python backend/main.py
    # Or with custom JSONL file
    uv run python backend/main.py -f /path/to/logs.jsonl

    # Start frontend (in another terminal)
    cd frontend
    npm install && npm run dev

    # Open browser to http://127.0.0.1:5173
    ```

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

alias uvr="uv run"
alias bd="bun dev"
```
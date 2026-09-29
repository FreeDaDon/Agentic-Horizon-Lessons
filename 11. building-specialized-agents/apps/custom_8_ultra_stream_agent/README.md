# Ultra Stream Agent

> Dual-agent system for real-time log stream processing and intelligent inspection

## Overview

Ultra Stream Agent demonstrates advanced multi-agent orchestration with two specialized Claude Agent SDK agents working in tandem:

- **Stream Agent**: Continuously processes streaming JSONL log files
- **Inspector Agent**: Provides intelligent query interface for processed logs

## Features

### Stream Agent Capabilities
- ✅ Continuous JSONL file processing in small batches
- ✅ Automatic log summarization and severity classification
- ✅ High-severity alert generation
- ✅ Context window management for infinite operation
- ✅ Real-time updates via WebSocket

### Inspector Agent Capabilities
- ✅ Natural language queries about log stream
- ✅ User-specific log investigation
- ✅ Pattern detection across logs
- ✅ Team notification system (Engineering & Support)
- ✅ Interactive chat interface

### Technical Highlights
- 🎯 Dual-panel Vue.js interface
- 🚀 FastAPI backend with WebSocket support
- 💾 SQLite database for persistence
- 🔄 Session continuity with resume capability
- 📊 Real-time statistics and monitoring

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Claude Code API key in `.env` file

### Setup

1. **Install Python dependencies**:
```bash
cd apps/custom_8_ultra_stream_agent
uv sync
```

2. **Install frontend dependencies**:
```bash
cd frontend
npm install
```

3. **Generate sample data**:
```bash
uv run python generate_sample_data.py
```

## Usage

### Start the Backend

```bash
# Default configuration
uv run python backend/main.py

# Custom JSONL file
uv run python backend/main.py -f /path/to/your/logs.jsonl

# Custom port
uv run python backend/main.py -p 8080
```

### Start the Frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

Open your browser to http://127.0.0.1:5173

## Architecture

### System Components

```
┌─────────────────────────────────────────┐
│            Vue.js Frontend              │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │  Inspector  │  │   Stream Panel    │ │
│  │    Panel    │  │  (Live Updates)   │ │
│  └─────────────┘  └──────────────────┘ │
└────────────────┬────────────────────────┘
                 │ WebSocket
┌────────────────▼────────────────────────┐
│           FastAPI Backend               │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │   Stream    │  │    Inspector     │ │
│  │    Agent    │  │      Agent       │ │
│  └─────────────┘  └──────────────────┘ │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼──────┐
         │   SQLite DB  │
         └──────────────┘
```

### Data Flow

1. **Stream Processing**:
   - JSONL file → Stream Agent → Summarized logs → Database → WebSocket → UI

2. **Inspection Flow**:
   - User query → Inspector Agent → Database query → Analysis → Response → UI

## Custom Tools

### Stream Agent Tools

| Tool                      | Purpose                       | Parameters                            |
| ------------------------- | ----------------------------- | ------------------------------------- |
| `read_stream_file`        | Read batch of JSONL lines     | `start_line_index`, `end_line_index`  |
| `produce_summarized_logs` | Store processed logs          | `summarized_logs[]`                   |
| `create_alert_message`    | Generate high-severity alerts | `alert_message`, `indices`, `user_id` |
| `clear_context`           | Reset context window          | None                                  |

### Inspector Agent Tools

| Tool                        | Purpose                   | Parameters                  |
| --------------------------- | ------------------------- | --------------------------- |
| `read_produced_log_entries` | Browse processed logs     | `start_index`, `end_index`  |
| `find_logs_for_user`        | Search user-specific logs | `user_id`, `limit`, `order` |
| `notify_engineering_team`   | Alert engineering team    | `alert_message`, `indices`  |
| `notify_support_team`       | Alert support team        | `alert_message`, `user_id`  |

## Example Interactions

### Inspector Agent Queries

```
"Show me all errors for user123"
"What happened in the payment service today?"
"Are there any database connection issues?"
"Find all high severity logs in the last hour"
"Show authentication failures"
```

### Automatic Alerts

The Stream Agent automatically generates alerts for:
- Critical errors (database failures, service outages)
- Error clusters (multiple errors for same user)
- System-wide issues (rate limiting, resource exhaustion)

## Database Schema

### produced_logs
- `id`: Primary key
- `log_index`: Original line number in JSONL
- `timestamp`: Processing timestamp
- `log_id`: Unique log identifier
- `log_summary`: AI-generated summary
- `log_severity`: low | medium | high
- `raw_data`: Original log JSON
- `user_id`: Associated user (optional)

### chat_messages
- `id`: Primary key
- `timestamp`: Message timestamp
- `message`: Text content
- `produced_log`: Associated log data
- `user_id`: User identifier
- `message_type`: user | assistant | alert | system

### session_information
- `current_line_index`: Current position in JSONL
- `stream_agent_session_id`: Stream agent session
- `inspector_agent_session_id`: Inspector agent session

## Development

### Project Structure

```
apps/custom_8_ultra_stream_agent/
├── backend/
│   └── main.py              # FastAPI server & agent logic
├── frontend/
│   ├── src/
│   │   ├── App.vue         # Main Vue component
│   │   └── main.js         # Entry point
│   └── package.json
├── modules/
│   └── data_types.py       # Pydantic models
├── system_prompts/
│   ├── stream_agent_system_prompt.md
│   └── inspector_agent_system_prompt.md
├── data/
│   └── ultra_stream_agent.jsonl  # Sample data
├── generate_sample_data.py
├── pyproject.toml
└── README.md
```

### Key Concepts Demonstrated

1. **Multi-Agent Orchestration**: Two specialized agents working together
2. **Stream Processing**: Handling continuous data streams efficiently
3. **Context Management**: Automatic context clearing for infinite operation
4. **Real-time Communication**: WebSocket for live updates
5. **Natural Language Interface**: Query logs using plain English
6. **Tool Composition**: Custom tools that work together
7. **Session Persistence**: Resume capability across restarts

## Monitoring

The UI displays real-time metrics:
- Active agent status
- Current line index
- Total logs processed
- Severity distribution
- Active connections

## Performance

- Processes ~100 logs/second
- Maintains <100ms WebSocket latency
- Automatic batch size optimization
- Context window management prevents overflow

## Troubleshooting

### Common Issues

1. **"Inspector Agent not initialized"**
   - Ensure ANTHROPIC_API_KEY is set in .env
   - Check backend logs for initialization errors

2. **No logs appearing**
   - Verify JSONL file path is correct
   - Check file permissions
   - Ensure file has valid JSON on each line

3. **WebSocket disconnection**
   - Frontend auto-reconnects after 3 seconds
   - Check network/firewall settings

4. **High memory usage**
   - Stream agent clears context every 50 logs
   - Adjust MAX_LINES_BEFORE_CONTEXT_CLEAR if needed

## Future Enhancements

- [ ] Multiple file support
- [ ] Real-time file tailing
- [ ] Custom alert rules
- [ ] Log export functionality
- [ ] Advanced filtering UI
- [ ] Metrics dashboard
- [ ] Distributed processing

## License

MIT
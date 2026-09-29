# Tri-Copy-Writer Agent

> **Purpose:** Professional copywriting with multiple variations and file context support
>
> **Level:** 3 (Advanced Web Interface + File Context + CLI Parameters + JSON Structure)

## Overview

The Tri-Copy-Writer Agent transforms copywriting workflows by providing multiple high-quality variations for any copy request. Unlike single-response tools, this agent provides one primary explanation plus multiple copy variations, giving marketers and content creators instant options and inspiration.

## Architecture

```
Frontend (Vue.js + Vite)  ←→  Backend (FastAPI + CLI)  ←→  Claude Agent SDK
     Port 5173                    Port 8000                  System Prompt
   Drag & Drop Files         File Context Processing         JSON Structure
   Copy to Clipboard         Version Control (-v flag)      Multi-Variations
```

### Key Features

- **Multiple Copy Variations**: Generate 1-10 variations (configurable via CLI `-v` flag)
- **Professional Interface**: Modern Vue.js frontend with copy-to-clipboard functionality
- **File Context Support**: Drag & drop text/markdown files for context
- **Structured Responses**: `{primary_response: "explanation", multi_version_copy_responses: ["v1", "v2", "v3"]}`
- **CLI Configuration**: Configurable number of variations via `--versions` parameter
- **Real-time Cost Tracking**: Session metadata with duration and API costs
- **Copy-to-Clipboard**: One-click copying of any variation

## Quick Start

### Prerequisites

- **Backend**: Python with `uv` (for dependency management)
- **Frontend**: Node.js with `npm` or `yarn`
- **Claude Code**: Installed and configured (`npm install -g @anthropic-ai/claude-code`)

### Backend Setup

```bash
# Navigate to backend directory
cd apps/custom_6_tri_copy_writer/backend

# Install dependencies
uv sync

# Start with default 3 variations
uv run python main.py

# Or configure custom number of variations (1-10)
uv run python main.py -v 5
uv run python main.py --versions 7
```

The backend will start on `http://127.0.0.1:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd apps/custom_6_tri_copy_writer/frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend will start on `http://127.0.0.1:5173`

### Usage

1. Open `http://127.0.0.1:5173` in your browser
2. Enter your copywriting request (e.g., "Write email subject lines for a product launch")
3. Optionally drag & drop text files for context
4. Receive one primary response + multiple copy variations
5. Click 📋 to copy any variation to clipboard

## System Prompt Design

Located at `prompts/TRI_COPY_WRITER_SYSTEM_PROMPT.md`, the system prompt:

- **Enforces JSON Structure**: Agent must respond in exact `{"primary_response": "...", "multi_version_copy_responses": [...]}` format
- **Accepts Dynamic Versions**: Uses `{NUMBER_OF_VERSIONS}` variable from CLI parameter
- **Handles File Context**: Processes `<content name="filename">...</content>` sections as background context
- **Copywriting Expertise**: Specialized prompts for headlines, email, social media, ads, etc.
- **Quality Standards**: Ensures each variation is distinct and ready-to-use

## API Endpoints

### `POST /copy`

Send a copywriting request and receive multiple variations.

**Request:**
```json
{
  "message": "Write headlines for a productivity app",
  "context_files": [
    {
      "name": "brand_guide.txt",
      "content": "Our brand voice is professional but friendly..."
    }
  ]
}
```

**Response:**
```json
{
  "copy_response": {
    "primary_response": "Here are headline variations focusing on productivity benefits and user pain points",
    "multi_version_copy_responses": [
      "Get 3x More Done in Half the Time",
      "Stop Drowning in Your To-Do List",
      "Finally, A Productivity App That Actually Works",
      "Transform Chaos Into Organized Success",
      "Your Personal Productivity Powerhouse"
    ]
  },
  "session_id": "abc123",
  "duration_ms": 2100,
  "cost_usd": 0.003245,
  "versions_generated": 5
}
```

### `GET /health`

Health check endpoint with version configuration info.

## File Context Features

### Drag & Drop Interface

- **Supported Files**: `.txt`, `.md`, and any `text/*` MIME type
- **Visual Feedback**: "Add Context" overlay appears on file drag
- **File Management**: View, update, and remove context files
- **Size Display**: Shows file size for each uploaded context file

### Context Processing

Files are processed as:
```xml
<content name="filename.txt">
...file content here...
</content>

User's copywriting request here
```

The AI uses file content as background context without responding to it directly.

## Development

### Project Structure

```
apps/custom_6_tri_copy_writer/
├── backend/
│   ├── main.py              # FastAPI application with CLI args
│   ├── pyproject.toml       # Python dependencies
│   └── requirements.txt     # Generated dependencies
├── frontend/
│   ├── src/
│   │   ├── App.vue         # Main Vue component with drag-drop
│   │   └── main.js         # Vue app entry point
│   ├── index.html          # HTML template
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite configuration
├── prompts/
│   └── TRI_COPY_WRITER_SYSTEM_PROMPT.md  # System prompt
└── README.md               # This file
```

### Key Technologies

- **Claude Agent SDK**: Python SDK for AI integration
- **FastAPI**: Modern Python web framework with CLI argument parsing
- **Vue.js 3**: Progressive JavaScript framework with drag-and-drop
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API communication

## CLI Configuration

The backend accepts command-line arguments:

```bash
# Default 3 variations
uv run python main.py

# Custom number of variations
uv run python main.py -v 5
uv run python main.py --versions 7

# View help
uv run python main.py --help
```

**Number of Versions:**
- Minimum: 1 variation
- Maximum: 10 variations
- Default: 3 variations
- Clamped automatically if outside range

## Learning Objectives

This agent demonstrates:

1. **CLI Parameter Integration**: How to make agents configurable via command-line arguments
2. **File Context Handling**: Processing uploaded files as background context
3. **Structured JSON Responses**: Enforcing specific response formats for different use cases
4. **Advanced UI Patterns**: Drag-and-drop, copy-to-clipboard, toast notifications
5. **Professional Workflow Integration**: Building tools that fit real copywriting workflows
6. **Error Handling**: Graceful degradation and user feedback
7. **Session Management**: Cost tracking and performance metrics

## Use Cases

### Email Marketing
```
Request: "Write subject lines for a Black Friday sale"
Context: Upload brand guidelines, previous campaign performance
Output: 5 subject line variations with different urgency levels
```

### Social Media
```
Request: "Create Instagram captions for a product launch"
Context: Upload product description, target audience info
Output: Multiple caption variations for different platforms
```

### Website Copy
```
Request: "Write homepage headlines for a SaaS tool"
Context: Upload competitor analysis, user research
Output: Headline variations focusing on different value propositions
```

### Ad Copy
```
Request: "Create Google Ads copy for a productivity app"
Context: Upload keyword research, landing page content
Output: Multiple ad variations with different angles
```

## Common Issues

### Backend Won't Start
- Ensure Claude Code CLI is installed: `npm install -g @anthropic-ai/claude-code`
- Check Python version compatibility (3.11+)
- Verify `uv` is installed: `pip install uv`

### Frontend Connection Errors
- Confirm backend is running on port 8000
- Check CORS configuration in `main.py`
- Verify API base URL in `App.vue`

### File Upload Issues
- Only text files and markdown are supported
- Check file size limits (frontend handles up to several MB)
- Ensure proper file encoding (UTF-8)

### Malformed AI Responses
- Review system prompt clarity in `TRI_COPY_WRITER_SYSTEM_PROMPT.md`
- Check Claude Code model selection
- Examine JSON parsing logic in backend `generate_copy_variations()`

## Extensions

Ideas for enhancing this agent:

- **Template Library**: Pre-built prompts for common copy types
- **A/B Testing**: Compare performance of different variations
- **Brand Voice Training**: Fine-tune responses to match brand guidelines
- **Integration APIs**: Connect to email platforms, CMS systems, social media
- **Analytics Dashboard**: Track which variations perform best
- **Collaboration Features**: Share and comment on copy variations
- **Version History**: Track changes and iterations over time

## Production Considerations

For deployment:

- **Environment Variables**: Move API configuration to environment variables
- **File Storage**: Implement proper file storage (S3, etc.) instead of in-memory
- **Rate Limiting**: Add request throttling to prevent abuse
- **Authentication**: Implement user accounts and API keys
- **Monitoring**: Add comprehensive logging and metrics
- **Caching**: Cache common requests to reduce API costs
- **Load Balancing**: Scale horizontally for multiple users
- **Database**: Store copy variations and user preferences
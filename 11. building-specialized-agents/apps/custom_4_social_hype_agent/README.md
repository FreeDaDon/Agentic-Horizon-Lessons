# Social Hype Agent

**Level 1.3**: Real-time social media content analysis with Bluesky WebSocket firehose monitoring

## Purpose

Monitor Bluesky social media firehose in real-time, filter posts by keywords, and use Claude Agent SDK to summarize and analyze sentiment of matching content.

## Capabilities

- **Real-time WebSocket monitoring** of Bluesky firehose
- **Keyword-based content filtering** with configurable search terms
- **Claude Agent SDK integration** for intelligent content analysis
- **Sentiment analysis** (positive, negative, neutral)
- **Automated summarization** of social media posts
- **CSV data storage** with continuous appending
- **Rich CLI interface** with progress tracking

## Architecture

```
Bluesky WebSocket → Keyword Filter → Claude Analysis → CSV Storage
    (firehose)       (contains)       (summarize)      (append)
```

## Usage

```bash
# Install dependencies
uv sync

# Monitor single keyword
uv run python social_hype_agent.py coding

# Monitor multiple keywords
uv run python social_hype_agent.py coding python javascript

# Monitor phrases (use quotes for multi-word phrases)
uv run python social_hype_agent.py "machine learning" "artificial intelligence"

# Mix phrases and keywords
uv run python social_hype_agent.py "claude code" python "web development"

# Custom output file
uv run python social_hype_agent.py coding --output coding_trends.csv
```

## CSV Output Format

| Column             | Description                                          |
| ------------------ | ---------------------------------------------------- |
| `matched_keywords` | Comma-separated list of matching keywords            |
| `sentiment`        | Sentiment classification (positive/negative/neutral) |
| `summary`          | Claude-generated summary (1-2 sentences)             |
| `original_text`    | Full text of the social media post                   |
| `raw_data`         | Full JSON data from Bluesky WebSocket                |

## Features

### Real-time Monitoring
- WebSocket connection to Bluesky firehose
- Processes posts as they are published
- Configurable match limits for testing

### Intelligent Analysis
- Claude Agent SDK for content summarization
- Structured sentiment analysis
- Fallback parsing for reliability

### Data Storage
- Automatic CSV file creation and management
- Continuous appending of results
- UTF-8 encoding for international content

## Dependencies

- `claude-agent-sdk`: AI-powered content analysis
- `websockets`: Real-time WebSocket connection
- `rich`: Beautiful terminal interface
- `python-dotenv`: Environment configuration

## Example Output

```
┌─ MATCH #1 ──────────────────────────────────────┐
│ Keywords: coding, python                         │
│ Text: Just finished a coding bootcamp...         │
└─ Post by @developer123 ─────────────────────────┘

┌─ Claude Analysis ───────────────────────────────┐
│ Summary: User completed coding bootcamp and is  │
│ excited about new programming skills            │
│ Sentiment: positive                              │
└──────────────────────────────────────────────────┘
```

## Key Learning Concepts

- **WebSocket integration** for real-time data streams
- **Claude Agent SDK query()** for AI-powered analysis
- **Structured data processing** with CSV output
- **Error handling** and fallback mechanisms
- **Asynchronous programming** patterns
- **CLI argument parsing** for user configuration

## Resources

- https://docs.bsky.app/docs/advanced-guides/firehose
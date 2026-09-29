# Pomodoro Timer CLI

A minimal Python CLI tool for managing focus sessions using the Pomodoro technique. Features beautiful terminal output with Rich, desktop notifications, and persistent session tracking.

## Features

- **Simple CLI Interface**: Start sessions with a single command
- **Configurable Duration**: Default 25-minute sessions or custom durations
- **Beautiful Terminal UI**: Full-width Rich panels with progress bars
- **Desktop Notifications**: Cross-platform notifications when sessions complete
- **Session Tracking**: Persistent storage of all sessions with statistics
- **Statistics Dashboard**: View total sessions, focus time, and recent activity
- **Keyboard Interrupt Handling**: Gracefully cancel sessions with Ctrl+C

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to the project directory
cd apps/pomodoro_timer

# Dependencies are automatically managed by UV
# No separate installation step needed!
```

## Usage

### Start a Pomodoro Session

Start a 25-minute session (default):
```bash
uv run python main.py start
```

Start a custom duration session (e.g., 45 minutes):
```bash
uv run python main.py start 45
```

### View Statistics

Display session statistics and recent activity:
```bash
uv run python main.py stats
```

### Check Version

```bash
uv run python main.py --version
```

### Get Help

```bash
uv run python main.py --help
uv run python main.py start --help
```

## Example Output

### Starting a Session
```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│ Starting Pomodoro Session                                │
│                                                          │
│ Duration: 25 minutes                                     │
│ Press Ctrl+C to cancel                                   │
│                                                          │
╰──────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────╮
│ Pomodoro Timer                                           │
│                                                          │
│ Duration: 25 minutes                                     │
│ Time Remaining: 24:59                                    │
│ Status: RUNNING                                          │
│                                                          │
│ Progress ████████████████░░░░░░░  60%  00:10:00        │
╰──────────────────────────────────────────────────────────╯
```

### Session Statistics
```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│ Session Statistics                                       │
│                                                          │
│ Total Sessions: 12                                       │
│ Completed Sessions: 10                                   │
│ Total Focus Time: 4h 10m                                 │
│ Average Session: 25.0 minutes                           │
│                                                          │
╰──────────────────────────────────────────────────────────╯

Recent Sessions (Last 5):

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Date            ┃ Duration  ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 2025-12-24 10:00│ 25 min    │ COMPLETED │
│ 2025-12-24 09:30│ 25 min    │ COMPLETED │
│ 2025-12-24 09:00│ 25 min    │ CANCELLED │
└─────────────────┴───────────┴───────────┘
```

## Configuration

### Environment Variables

You can customize the data storage location using environment variables:

Create a `.env` file in the project directory:
```bash
# Custom data directory (optional)
POMODORO_DATA_DIR=~/my-pomodoro-data
```

### Default Storage Location

By default, session data is stored in:
```
~/.pomodoro_timer/
├── sessions.json          # Session history
└── current_session.json   # Current session state
```

## Data Storage

Sessions are stored in JSON format with the following structure:

```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "duration_minutes": 25,
      "start_time": "2025-12-24T10:00:00",
      "end_time": "2025-12-24T10:25:00",
      "pause_duration_seconds": 0,
      "status": "COMPLETED",
      "completed": true
    }
  ]
}
```

## Architecture

The application follows a clean architecture with separated concerns:

- **models.py**: Pydantic data models for type-safe data structures
- **storage.py**: JSON-based persistence layer for session data
- **timer.py**: Core timer logic with Rich UI display
- **notifications.py**: Desktop notification integration using plyer
- **config.py**: Configuration management with environment variable support
- **main.py**: Typer-based CLI commands and session state management

## Dependencies

- **typer**: CLI framework
- **rich**: Beautiful terminal output
- **pydantic**: Data validation and models
- **python-dotenv**: Environment variable management
- **plyer**: Cross-platform desktop notifications

All dependencies are automatically managed by UV through `pyproject.toml`.

## Session States

- **NOT_STARTED**: Session created but not started
- **RUNNING**: Session actively counting down
- **PAUSED**: Session paused (note: pause/resume not fully implemented)
- **COMPLETED**: Session finished successfully
- **CANCELLED**: Session cancelled by user (Ctrl+C)

## Notes

### Pause/Resume Functionality

The pause and resume commands are included in the CLI but require running the timer in a separate process to work fully. For now, use Ctrl+C to cancel a session and start a new one if needed.

### Notification Support

Desktop notifications use the `plyer` library for cross-platform support. If notifications don't work on your platform, the application will continue to function normally with a warning message.

### Error Handling

The application gracefully handles:
- Missing or corrupted storage files
- Invalid session states
- Notification failures
- Keyboard interrupts (Ctrl+C)

## Future Enhancements

Potential features for future versions:
- Break timer functionality
- Sound alerts
- Session tags/categories
- Export stats to CSV
- Integration with calendar apps
- Web dashboard

## License

This is an internal tool built for personal productivity.

## Development

### Project Structure
```
apps/pomodoro_timer/
├── main.py              # CLI entry point
├── models.py            # Data models
├── timer.py             # Timer logic
├── storage.py           # Persistence layer
├── notifications.py     # Notification integration
├── config.py            # Configuration management
├── pyproject.toml       # UV project configuration
├── .gitignore          # Git ignore patterns
└── README.md           # This file
```

### Running Tests

Manual testing workflow:
1. Start a 1-minute test session: `uv run python main.py start 1`
2. Let it complete and verify notification
3. Check stats: `uv run python main.py stats`
4. Start another session and cancel with Ctrl+C
5. Verify both sessions appear in stats

## Support

For issues or feature requests, please contact the development team.

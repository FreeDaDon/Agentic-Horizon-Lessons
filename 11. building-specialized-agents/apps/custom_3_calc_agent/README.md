# Calculator Agent - Level 1.2

An interactive calculator agent with custom tools for mathematical calculations and unit conversions. This agent demonstrates advanced Claude Agent SDK features including custom tool creation, MCP server configuration, and REPL functionality.

## Features

### 🧮 Mathematical Calculations
- **Basic arithmetic**: `+`, `-`, `*`, `/`, `**`, `%`
- **Mathematical functions**: `sin`, `cos`, `tan`, `sqrt`, `log`, `exp`, etc.
- **Precision control**: Specify decimal places for results
- **Safe evaluation**: Restricted scope for security

### 📏 Unit Conversions
- **Length**: meters, kilometers, centimeters, millimeters, feet, inches, miles
- **Weight**: kilograms, grams, milligrams, pounds, ounces
- **Temperature**: Celsius, Fahrenheit, Kelvin

### 💬 Interactive REPL with TRUE Session Continuity
- **True session continuity**: Remembers all previous calculations and context
- **Session resumption**: Uses `resume=session_id` to maintain conversation history
- Rich terminal interface with colored output
- Session cost tracking
- Graceful error handling
- Easy exit with `quit` or `exit`

## Installation

```bash
# Navigate to the project directory
cd apps/custom_3_calc_agent

# Install dependencies with uv
uv sync

# Alternative: Install dependencies with pip
pip install -r requirements.txt
```

## Usage

### Start the Calculator Agent

```bash
uv run python calc_agent.py
```

### Example Interactions

**Mathematical Calculations:**
```
Calculator: Calculate the area of a circle with radius 10
🤖 Calculator Agent: I'll calculate the area of a circle with radius 10.

The formula for the area of a circle is A = π × r²

🔧 Using calculate tool...
Result: 314.16

So the area of a circle with radius 10 is 314.16 square units.
```

**Unit Conversions:**
```
Calculator: Convert 100 fahrenheit to celsius
🤖 Calculator Agent: I'll convert 100 degrees Fahrenheit to Celsius.

🔧 Using convert_units tool...
100.0 F = 37.7778 C

So 100°F equals approximately 37.78°C.
```

**Advanced Math:**
```
Calculator: What's the square root of 144 plus the sine of pi/2?
🤖 Calculator Agent: I'll calculate the square root of 144 plus the sine of π/2.

🔧 Using calculate tool...
Result: 13.0

The square root of 144 is 12, and sin(π/2) is 1, so 12 + 1 = 13.
```

## Technical Implementation

### Custom Tools

The agent uses two custom tools created with the `@tool` decorator:

1. **`calculate_expression`**: Safely evaluates mathematical expressions
2. **`convert_measurement_units`**: Handles unit conversions between different measurement systems

### MCP Server Configuration

```python
calculator_mcp_server = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[calculate_expression, convert_measurement_units]
)

# Base options for session resumption
base_options = {
    "mcp_servers": {"calculator": calculator_mcp_server},
    "allowed_tools": [
        "mcp__calculator__custom_math_evaluator",
        "mcp__calculator__custom_unit_converter",
    ],
    "system_prompt": "...Remember our conversation history...",
    "model": "claude-sonnet-4-20250514",
}
```

### ClaudeSDKClient Features

- **TRUE Session Continuity**: Uses session resumption approach to maintain context across ALL queries
- **Custom system prompt**: Specialized for mathematical tasks with memory instructions
- **Tool integration**: Seamless access to custom calculation functions
- **Session state management**: Captures and reuses session_id for conversation history
- **Error handling**: Graceful handling of calculation and conversion errors

## Project Structure

```
apps/custom_3_calc_agent/
├── calc_agent.py          # Main calculator agent implementation
├── pyproject.toml         # Project dependencies and metadata
└── README.md             # This file
```

## Key Learning Points

This agent demonstrates:

- **Custom Tool Creation**: Using `@tool` decorator for domain-specific functions
- **Tool Composition**: Multiple tools working together in one agent
- **Error Handling**: Proper error handling in custom tools
- **TRUE REPL Interface**: Building interactive conversational agents with session continuity
- **Session Resumption**: Using `resume=session_id` parameter for maintaining conversation history
- **MCP Integration**: Creating and configuring MCP servers
- **Safe Code Execution**: Restricted evaluation scope for security
- **Session State Management**: Capturing and reusing session_id from ResultMessage

## Dependencies

- `claude-agent-sdk`: Claude Agent SDK
- `rich`: Beautiful terminal output and formatting

## Advanced Usage

### Precision Control
```
Calculator: Calculate pi to 6 decimal places
```

### Complex Expressions
```
Calculator: What's the result of 2^10 * sqrt(16) + log(100)?
```

### Multiple Conversions
```
Calculator: Convert 5 feet 6 inches to meters
```

## Exit Commands

To exit the calculator REPL:
- Type `quit`
- Type `exit`
- Type `q`
- Press `Ctrl+C`

## Error Handling

The agent handles various error conditions:
- Invalid mathematical expressions
- Unsupported unit conversions
- Network connectivity issues
- Malformed inputs

All errors are displayed with helpful messages and the agent continues running.

---

**Level**: 1.2 - Custom Tool Creation with Session Continuity
**SDK Features**: `@tool`, `create_sdk_mcp_server`, `ClaudeSDKClient`, session resumption, REPL pattern
**Advanced Features**: Session state management, conversation history, memory across exchanges
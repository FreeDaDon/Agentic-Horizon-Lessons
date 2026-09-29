#!/usr/bin/env python3
"""
Calculator Agent - Level 1.2
An interactive calculator agent with custom tools for mathematical calculations and unit conversions.
This demonstrates:
- Custom tool creation with @tool decorator
- MCP server creation and configuration
- Interactive REPL functionality with TRUE session continuity
- Error handling in custom tools
- Session resumption approach for maintaining conversation history
"""

import asyncio
import math
from pathlib import Path
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
)

# Create a rich console for beautiful terminal output
console = Console()


def load_system_prompt() -> str:
    """
    Load the system prompt from the markdown file.
    Returns the content of the prompt file.
    """
    prompt_file = Path(__file__).parent / "prompts" / "CALC_AGENT_SYSTEM_PROMPT.md"

    with open(prompt_file, "r") as file:
        system_prompt = file.read().strip()

    return system_prompt


@tool(
    "custom_math_evaluator",
    "Perform mathematical calculations",
    {"expression": str, "precision": int},
)
async def calculate_expression(args: dict[str, Any]) -> dict[str, Any]:
    """
    Safely evaluate mathematical expressions with limited scope for security.
    Supports basic math operations and common mathematical functions.
    """
    try:
        # Create a safe namespace with math functions
        allowed_math_functions = {
            function_name: function_value
            for function_name, function_value in math.__dict__.items()
            if not function_name.startswith("_")
        }

        # Add additional safe functions
        allowed_math_functions.update(
            {"abs": abs, "round": round, "min": min, "max": max, "sum": sum}
        )

        # Evaluate the expression safely
        calculation_result = eval(
            args["expression"], {"__builtins__": {}}, allowed_math_functions
        )

        # Apply precision formatting
        precision_value = args.get("precision", 2)

        if isinstance(calculation_result, float):
            formatted_result = round(calculation_result, precision_value)
        else:
            formatted_result = calculation_result

        return {"content": [{"type": "text", "text": f"Result: {formatted_result}"}]}
    except Exception as calculation_error:
        return {
            "content": [
                {"type": "text", "text": f"Calculation error: {str(calculation_error)}"}
            ],
            "is_error": True,
        }


@tool(
    "custom_unit_converter",
    "Convert between measurement units",
    {"value": float, "from_unit": str, "to_unit": str},
)
async def convert_measurement_units(args: dict[str, Any]) -> dict[str, Any]:
    """
    Convert between common units including length, weight, and temperature.
    Supports metric and imperial systems.
    """

    # Conversion factors to base units for easy calculation
    unit_conversion_factors = {
        # Length conversions (to meters)
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "ft": 0.3048,
        "in": 0.0254,
        "mi": 1609.34,
        # Weight conversions (to kilograms)
        "kg": 1.0,
        "g": 0.001,
        "mg": 0.000001,
        "lb": 0.453592,
        "oz": 0.0283495,
        # Temperature units (special handling required)
        "C": "celsius",
        "F": "fahrenheit",
        "K": "kelvin",
    }

    input_value = args["value"]
    source_unit = args["from_unit"]
    target_unit = args["to_unit"]

    try:
        # Handle temperature conversions separately due to offset calculations
        if source_unit in ["C", "F", "K"] and target_unit in ["C", "F", "K"]:
            converted_value = convert_temperature(input_value, source_unit, target_unit)
        else:
            # Handle regular unit conversions using multiplication factors
            if (
                source_unit not in unit_conversion_factors
                or target_unit not in unit_conversion_factors
            ):
                raise ValueError(
                    f"Unsupported unit conversion: {source_unit} to {target_unit}"
                )

            # Convert to base unit first, then to target unit
            base_unit_value = input_value * unit_conversion_factors[source_unit]
            converted_value = base_unit_value / unit_conversion_factors[target_unit]

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"{input_value} {source_unit} = {converted_value:.4f} {target_unit}",
                }
            ]
        }
    except Exception as conversion_error:
        return {
            "content": [
                {"type": "text", "text": f"Conversion error: {str(conversion_error)}"}
            ],
            "is_error": True,
        }


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    Helper function to handle temperature conversions.
    Temperature conversions require offset calculations, not just multiplication.
    """
    if from_unit == to_unit:
        return value

    # Convert from Celsius
    if from_unit == "C":
        if to_unit == "F":
            return (value * 9 / 5) + 32
        elif to_unit == "K":
            return value + 273.15

    # Convert from Fahrenheit
    elif from_unit == "F":
        if to_unit == "C":
            return (value - 32) * 5 / 9
        elif to_unit == "K":
            return (value - 32) * 5 / 9 + 273.15

    # Convert from Kelvin
    elif from_unit == "K":
        if to_unit == "C":
            return value - 273.15
        elif to_unit == "F":
            return (value - 273.15) * 9 / 5 + 32

    return value


async def run_calculator_repl():
    """
    Run the calculator agent in REPL mode with TRUE session continuity.
    Uses session resumption approach to maintain conversation history across queries.
    """

    # Step 1: Create MCP server following docs pattern exactly
    calculator_mcp_server = create_sdk_mcp_server(
        name="calculator",
        version="1.0.0",
        tools=[
            calculate_expression,
            convert_measurement_units,
        ],  # Pass decorated functions
    )

    # Step 2: Load the system prompt from the markdown file
    calculator_system_prompt = load_system_prompt()

    # Step 3: Display startup banner
    startup_banner = Text.assemble(
        ("🧮 ", "bold blue"),
        ("Calculator Agent REPL", "bold cyan"),
        (" - True Session Continuity", "bold green"),
    )

    startup_panel = Panel.fit(
        startup_banner, border_style="cyan", subtitle="Type 'quit' or 'exit' to stop"
    )
    console.print(startup_panel)
    console.print()

    # Display helpful usage examples
    examples_table = Table(
        title="Example Commands", show_header=True, title_style="bold yellow"
    )
    examples_table.add_column("Type", style="cyan", no_wrap=True)
    examples_table.add_column("Example", style="green")

    examples_table.add_row("Math", "Calculate the area of a circle with radius 10")
    examples_table.add_row("Math", "What's the square root of 144?")
    examples_table.add_row("Units", "Convert 100 fahrenheit to celsius")
    examples_table.add_row("Memory", "What was my last calculation?")

    console.print(examples_table)
    console.print()

    # Step 4: Track session for TRUE continuity and cost tracking
    current_session_id = None
    total_session_cost = 0.0

    # Main REPL loop with session continuity using resume parameter
    while True:
        try:
            # Get user input with rich prompt
            user_input = Prompt.ask(
                "[bold blue]Calculator[/bold blue]",
            ).strip()

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "q"]:
                # Display final cost summary
                if total_session_cost > 0:
                    cost_summary = f"💰 Total Session Cost: ${total_session_cost:.6f}"
                    console.print(f"[bold yellow]{cost_summary}[/bold yellow]")
                    console.print()

                farewell_message = (
                    "[bold green]👋 Thanks for using Calculator Agent![/bold green]"
                )
                console.print(Panel.fit(farewell_message, border_style="green"))
                break

            # Skip empty inputs
            if not user_input:
                continue

            # Display user input in a panel
            console.print(Panel(user_input, title="User Prompt", border_style="yellow"))

            # Create options with resume parameter for session continuity
            calculator_agent_options = ClaudeAgentOptions(
                mcp_servers={"calculator": calculator_mcp_server},
                allowed_tools=[
                    "mcp__calculator__custom_math_evaluator",  # Allow math evaluator tool
                    "mcp__calculator__custom_unit_converter",  # Allow unit converter tool
                ],
                disallowed_tools=[
                    # Disable all built-in tools - calculator only needs custom tools
                    "Read",
                    "Write",
                    "Edit",
                    "MultiEdit",
                    "NotebookEdit",  # File management
                    "Glob",
                    "Grep",  # Search & discovery
                    "WebFetch",
                    "WebSearch",  # Web tools
                    "TodoWrite",
                    "Task",
                    "ExitPlanMode",  # Task management
                    "Bash",
                    "BashOutput",
                    "KillShell",  # System tools
                ],
                system_prompt=calculator_system_prompt,
                model="claude-sonnet-4-20250514",  # Fast model for calculations
                resume=current_session_id,  # KEY: Resume existing session for continuity!
            )

            # Create streaming input format required for custom tools
            async def create_message_generator():
                yield {
                    "type": "user",
                    "message": {"role": "user", "content": user_input},
                }

            # Use ClaudeSDKClient with session resumption
            async with ClaudeSDKClient(options=calculator_agent_options) as client:

                # Send query to calculator agent using streaming format
                await client.query(create_message_generator())

                # Process and display the response
                response_received = False

                async for message in client.receive_response():

                    # Handle assistant responses
                    if isinstance(message, AssistantMessage):
                        for content_block in message.content:
                            if isinstance(content_block, TextBlock):
                                # Display the agent's text response
                                console.print(
                                    Panel(
                                        content_block.text,
                                        title="Agent Response",
                                        border_style="green",
                                    )
                                )
                                response_received = True

                            elif isinstance(content_block, ToolUseBlock):
                                # Show which tool is being used
                                console.print(
                                    Panel(
                                        f"{content_block.name}",
                                        title="Tool Called",
                                        border_style="cyan",
                                        style="dim",
                                    )
                                )

                    # Handle result messages for session stats and session_id capture
                    elif isinstance(message, ResultMessage):
                        # CRITICAL: Capture session_id for next query to maintain continuity
                        if message.session_id:
                            current_session_id = message.session_id

                        # Track and show cost information
                        if message.total_cost_usd:
                            total_session_cost += message.total_cost_usd
                            cost_info = f"💰 Query Cost: ${message.total_cost_usd:.6f} | Session Total: ${total_session_cost:.6f}"
                            console.print(f"[dim yellow]{cost_info}[/dim yellow]")

                # Add spacing between interactions
                console.print()

                # Show error if no response received
                if not response_received:
                    error_message = "[bold red]❌ No response received from calculator agent[/bold red]"
                    console.print(error_message)
                    console.print()

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            console.print("\n[bold yellow]⚠️  Interrupted by user[/bold yellow]")
            break
        except EOFError:
            # Handle EOF gracefully when not in interactive mode
            console.print("\n[bold yellow]⚠️  EOF detected - exiting[/bold yellow]")
            break
        except Exception as repl_error:
            # Handle unexpected errors
            error_message = f"[bold red]❌ Error: {str(repl_error)}[/bold red]"
            console.print(error_message)
            console.print()


async def main():
    """
    Main entry point for the calculator agent.
    Starts the REPL interface for interactive calculations with session continuity.
    """
    await run_calculator_repl()


if __name__ == "__main__":
    asyncio.run(main())

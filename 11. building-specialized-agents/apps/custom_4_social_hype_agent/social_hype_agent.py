#!/usr/bin/env python3
"""
Social Hype Agent v4 - Modular Architecture

Real-time Bluesky WebSocket firehose monitor with:
- AI-powered content analysis
- Intelligent notification system
- Text-to-speech audio alerts
- Modular, maintainable codebase

Usage:
    python social_hype_agent.py <keywords> -n <notification_criteria>

Example:
    python social_hype_agent.py "claude" "gpt" -n "Notify me about major AI announcements"
"""

import asyncio
import argparse
import sys
from rich.console import Console

# Import from our modules
from modules import SocialHypeAgent


async def main():
    """
    Main entry point for the Social Hype Agent.

    Parses command line arguments and runs the monitoring agent.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Social Hype Agent v4 - Monitor Bluesky with AI analysis and smart notifications"
    )

    parser.add_argument(
        "keywords",
        nargs="+",
        help="Keywords or phrases to monitor (use quotes for phrases: 'claude code' 'machine learning')",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="social_hype_results.csv",
        help="Output CSV file path (default: social_hype_results.csv)",
    )

    parser.add_argument(
        "--notify-prompt",
        "-n",
        required=True,
        help="REQUIRED: Notification criteria prompt (e.g., 'Notify me when there are mentions of product launches or breaking news')",
    )

    args = parser.parse_args()

    # Initialize console for output
    console = Console()

    # Display startup banner
    console.print("[bold cyan]🚀 Social Hype Agent[/bold cyan]")
    console.print("[dim]Real-time social monitoring with AI analysis[/dim]")
    console.print()

    try:
        # Create and run agent
        agent = SocialHypeAgent(
            keywords=args.keywords,
            output_file=args.output,
            notification_prompt=args.notify_prompt,
        )

        # Run the monitoring loop
        await agent.monitor()

    except KeyboardInterrupt:
        console.print("\n[yellow]⏸️  Monitoring stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Agent error: {e}[/red]")
        sys.exit(1)
    finally:
        # Show final statistics if agent exists
        if "agent" in locals():
            agent.show_stats()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)

"""
Social Hype Agent Module

Main agent class for monitoring and analyzing social media content.
Handles WebSocket connections, content processing, and Claude Agent SDK integration.
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import websockets
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)

# Import local modules
from .tools import submit_analysis_tool, notify_tool
from .utils import MatchedPost, load_system_prompt


class SocialHypeAgent:
    """
    Social media hype tracking agent using Bluesky WebSocket firehose.

    Features:
    - Real-time WebSocket monitoring
    - Non-blocking queue system
    - Intelligent notifications
    - Claude Agent SDK integration
    """

    def __init__(
        self,
        keywords: List[str],
        output_file: str = "social_hype_results.csv",
        notification_prompt: str = None,
    ):
        """
        Initialize the Social Hype Agent.

        Args:
            keywords: List of keywords to monitor
            output_file: Path to CSV output file
            notification_prompt: Required notification criteria

        Raises:
            ValueError: If notification_prompt is not provided
        """
        # Require notification prompt to be specified
        if not notification_prompt:
            raise ValueError(
                "notification_prompt is required. Please specify your notification criteria using the -n flag.\n"
                'Example: -n "Notify me when there are mentions of major product launches or breaking news"'
            )

        # Initialize basic attributes
        self.keywords = [keyword.lower() for keyword in keywords]
        self.output_file = Path(output_file)
        self.console = Console()
        self.ws = None
        self.matches_found = 0
        self.processed_count = 0
        self.running = True

        # Queue system for non-blocking processing
        self.match_queue = asyncio.Queue(maxsize=100)
        self.queue_processed = 0
        self.notifications_sent = 0

        # Cost tracking variable (updated from ResultMessage)
        self.total_cost_usd = 0.0

        # Store notification criteria
        self.notification_criteria = notification_prompt

        # Load system prompt from external file with variable substitution
        self.analysis_prompt = load_system_prompt(self.notification_criteria)

        # Setup Claude client with custom tools for analysis and notifications
        self.tools_server = create_sdk_mcp_server(
            name="social_tools",
            version="1.0.0",
            tools=[submit_analysis_tool, notify_tool],
        )

        self.claude_options = ClaudeAgentOptions(
            system_prompt=self.analysis_prompt,
            model="sonnet",
            mcp_servers={"tools": self.tools_server},
            allowed_tools=["mcp__tools__submit_analysis", "mcp__tools__notify"],
            disallowed_tools=[
                # Disable all built-in tools
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
            max_turns=3,  # Allow for both analysis and notification
        )

        # Initialize CSV file with headers
        self._initialize_csv()

    def _initialize_csv(self):
        """
        Initialize CSV file with headers if it doesn't exist or is missing headers.
        """
        expected_headers = [
            "timestamp",
            "matched_keywords",
            "sentiment",
            "summary",
            "original_text",
            "raw_data",
        ]

        # Check if file exists and has headers
        needs_headers = False

        if not self.output_file.exists():
            needs_headers = True
        else:
            # Check if file is empty or doesn't have correct headers
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    try:
                        first_row = next(reader)
                        # Check if first row looks like headers (not a timestamp)
                        if not first_row or not first_row[0] == "timestamp":
                            needs_headers = True
                    except StopIteration:
                        # File is empty
                        needs_headers = True
            except Exception:
                needs_headers = True

        # Write headers if needed
        if needs_headers:
            # If file exists with data, rename it as backup
            if self.output_file.exists() and self.output_file.stat().st_size > 0:
                backup_file = self.output_file.with_suffix(".csv.bak")

                # Read existing data
                with open(self.output_file, "r", encoding="utf-8") as f:
                    existing_data = f.read()

                # Write backup silently
                with open(backup_file, "w", encoding="utf-8") as f:
                    f.write(existing_data)

                # Write headers and existing data to original file
                with open(self.output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(expected_headers)

                    # Append existing data if any
                    if existing_data.strip():
                        f.write(existing_data)
            else:
                # Just create new file with headers
                with open(self.output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(expected_headers)

    def _filter_content(self, text: str) -> List[str]:
        """
        Check if text contains any keywords.

        Args:
            text: Text to check

        Returns:
            List of matched keywords
        """
        if not text:
            return []

        text_lower = text.lower()
        matched = []

        for keyword in self.keywords:
            if keyword in text_lower:
                matched.append(keyword)

        return matched

    async def _analyze_and_notify(
        self, text: str, matched_keywords: List[str]
    ) -> Dict[str, str]:
        """
        Use Claude Agent SDK with custom tools for content analysis.

        Claude will use submit_analysis tool to provide analysis
        and optionally notify tool for important content.

        Args:
            text: Content to analyze

        Returns:
            Dictionary with analysis results
        """
        try:
            async with ClaudeSDKClient(options=self.claude_options) as client:
                # Include matched keywords in the prompt for context
                prompt = f"""Post content matched on keywords: {', '.join(matched_keywords)}

{text}"""

                await client.query(prompt)

                # Initialize variables to capture tool responses
                summary = "No analysis provided"
                sentiment = "neutral"
                notification_sent = False
                full_response = ""

                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                full_response += block.text

                            elif isinstance(block, ToolUseBlock):
                                # Handle submit_analysis tool call
                                if block.name == "mcp__tools__submit_analysis":
                                    # Extract summary, sentiment, and keyword from tool input
                                    summary = block.input.get(
                                        "summary", "No summary provided"
                                    )
                                    sentiment = block.input.get("sentiment", "neutral")
                                    keyword = block.input.get("keyword", "unknown")

                                    # Add newline for visual separation
                                    self.console.print()

                                    # Create consistent block format like calc agent
                                    analysis_panel = Panel(
                                        f"Keyword: {keyword}\nSentiment: {sentiment}",
                                        title="Tool Called: submit_analysis",
                                        border_style="cyan",
                                    )
                                    self.console.print(analysis_panel)

                                # Handle notify tool call
                                elif block.name == "mcp__tools__notify":
                                    notification_sent = True
                                    self.notifications_sent += 1

                                    # Get notification details
                                    notify_title = block.input.get("title", "No title")
                                    notify_message = block.input.get(
                                        "message", "No message"
                                    )
                                    notify_urgency = block.input.get(
                                        "urgency", "normal"
                                    )

                                    # Add newline for visual separation
                                    self.console.print()

                                    # Create consistent notification panel
                                    notify_content = (
                                        f"Title: {notify_title}\n"
                                        f"Message: {notify_message}\n"
                                        f"Urgency: {notify_urgency}\n"
                                        f"Total sent: {self.notifications_sent}"
                                    )

                                    notify_panel = Panel(
                                        notify_content,
                                        title="Tool Called: notify",
                                        border_style="purple",
                                    )
                                    self.console.print(notify_panel)

                            elif isinstance(block, ToolResultBlock):
                                # Debug: Show tool result responses
                                if block.tool_use_id:
                                    if block.is_error:
                                        self.console.print(
                                            f"[red]❌ Tool error: {block.content}[/red]"
                                        )
                                    else:
                                        self.console.print(
                                            f"[green]✅ Tool result: {block.content}[/green]"
                                        )

                    elif isinstance(message, ResultMessage):
                        # Update total cost from ResultMessage
                        if message.total_cost_usd is not None:
                            self.total_cost_usd += message.total_cost_usd

                return {
                    "summary": summary,
                    "sentiment": sentiment,
                    "notification_sent": notification_sent,
                    "full_analysis": full_response,
                }

        except Exception as e:
            self.console.print(f"[red]Error analyzing content: {e}[/red]")
            return {
                "summary": f"Analysis failed: {str(e)}",
                "sentiment": "unknown",
                "notification_sent": False,
                "full_analysis": "",
            }

    async def _process_queue_worker(self):
        """
        Async worker that processes matches from the queue.

        Runs concurrently with WebSocket ingestion to avoid blocking.
        """
        # Queue processor status will be shown in the main table
        while self.running:
            try:
                # Wait for a match to process (with timeout to allow clean shutdown)
                try:
                    matched_post = await asyncio.wait_for(
                        self.match_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process the match with Claude (includes notification decision)
                self.console.print(
                    f"[blue]📝 Analyzing match #{matched_post.match_number} with Claude...[/blue]"
                )
                analysis_data = await self._analyze_and_notify(
                    matched_post.post_text, matched_post.matched_keywords
                )

                # Save to CSV
                self._save_to_csv(
                    matched_post.post_data, matched_post.matched_keywords, analysis_data
                )

                self.queue_processed += 1

                # Show Claude analysis results
                notification_status = (
                    "🔔 Notified"
                    if analysis_data["notification_sent"]
                    else "🔕 No notification"
                )

                # Add newline for visual separation
                self.console.print()

                # Show Claude analysis results in consistent block format
                self.console.print(
                    Panel(
                        f"Summary: {analysis_data['summary']}\n"
                        f"Sentiment: {analysis_data['sentiment']}\n"
                        f"Notification: {notification_status}",
                        title="Agent Response",
                        border_style="green",
                    )
                )

                # Mark task as done
                self.match_queue.task_done()

            except Exception as e:
                self.console.print(f"[red]Error in queue worker: {e}[/red]")
                continue

        self.console.print("[yellow]📥 Queue processor stopped[/yellow]")

    def _save_to_csv(
        self,
        post_data: Dict[str, Any],
        matched_keywords: List[str],
        analysis_data: Dict[str, str],
    ):
        """
        Save processed data to CSV file.

        Args:
            post_data: Raw post data
            matched_keywords: Keywords that matched
            analysis_data: Analysis results from Claude
        """
        try:
            with open(self.output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Extract relevant fields from post data
                original_text = (
                    post_data.get("commit", {}).get("record", {}).get("text", "")
                )

                writer.writerow(
                    [
                        datetime.now().isoformat(),
                        ", ".join(matched_keywords),
                        analysis_data.get("sentiment", ""),
                        analysis_data.get("summary", ""),
                        original_text,
                        json.dumps(post_data, separators=(",", ":")),
                    ]
                )

                self.console.print(
                    f"[green]✓ Saved match #{self.queue_processed} to CSV[/green]"
                )
        except Exception as e:
            self.console.print(f"[red]Failed to save to CSV: {e}[/red]")

    async def monitor(self):
        """
        Main monitoring loop for the WebSocket firehose.

        Connects to Bluesky WebSocket and processes incoming posts.
        """
        uri = "wss://jetstream2.us-west.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

        # Start queue processor in background
        queue_task = asyncio.create_task(self._process_queue_worker())

        try:
            async with websockets.connect(uri) as websocket:
                self.ws = websocket

                # Display monitoring configuration and status in a rich table
                config_table = Table(
                    title="🚀 Social Hype Agent Connected",
                    show_header=True,
                    title_style="bold green",
                )
                config_table.add_column("Status/Setting", style="yellow", width=25)
                config_table.add_column("Value", style="white")

                # Add connection status
                config_table.add_row(
                    "Connection", "[green]✅ Connected to Bluesky firehose[/green]"
                )

                # Add queue processor status
                config_table.add_row(
                    "Queue Processor", "[green]🔄 Running with notifications[/green]"
                )

                # Add keywords row
                config_table.add_row("Keywords", ", ".join(self.keywords))

                # Add notification prompt row
                config_table.add_row("Notification Prompt", self.notification_criteria)

                # Add output file row
                config_table.add_row("Output File", str(self.output_file))

                self.console.print(config_table)
                self.console.print()

                with Progress() as progress:
                    task = progress.add_task("[cyan]Processing posts...", total=None)

                    while self.running:
                        try:
                            # Receive message from WebSocket
                            message = await asyncio.wait_for(
                                websocket.recv(), timeout=30.0
                            )
                            data = json.loads(message)
                            self.processed_count += 1

                            # Extract post text
                            post_text = (
                                data.get("commit", {}).get("record", {}).get("text", "")
                            )

                            # Check for keyword matches
                            matched_keywords = self._filter_content(post_text)

                            if matched_keywords:
                                self.matches_found += 1

                                # Create matched post object
                                matched_post = MatchedPost(
                                    post_data=data,
                                    post_text=post_text,
                                    matched_keywords=matched_keywords,
                                    match_number=self.matches_found,
                                )

                                # Add to queue if not full
                                if not self.match_queue.full():
                                    await self.match_queue.put(matched_post)

                                    # Add newline for visual separation
                                    self.console.print()

                                    # Show match notification in panel
                                    match_panel = Panel(
                                        f"Match #{self.matches_found}\nKeywords: {', '.join(matched_keywords)}",
                                        title="Match Found",
                                        border_style="yellow",
                                    )
                                    self.console.print(match_panel)
                                else:
                                    self.console.print(
                                        "[red]⚠️ Queue full, skipping match[/red]"
                                    )

                            # Update progress
                            progress.update(
                                task,
                                description=(
                                    f"Processed: {self.processed_count} | "
                                    f"Matched: {self.matches_found} | "
                                    f"Analyzed: {self.queue_processed} | "
                                    f"Notified: {self.notifications_sent}"
                                ),
                            )

                        except asyncio.TimeoutError:
                            self.console.print(
                                "[yellow]⏱️ No messages for 30s, still listening...[/yellow]"
                            )
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.console.print(f"[bold red]❌ Error: {e}[/bold red]")
        finally:
            self.running = False
            await queue_task
            self.console.print("[red]Connection closed[/red]")

    def show_stats(self):
        """
        Display final statistics for the monitoring session.
        """
        stats = Table(title="📊 Session Statistics", show_header=True)
        stats.add_column("Metric", style="cyan")
        stats.add_column("Value", style="yellow")

        stats.add_row("Total Processed", str(self.processed_count))
        stats.add_row("Matches Found", str(self.matches_found))
        stats.add_row("Analyzed", str(self.queue_processed))
        stats.add_row("Notifications Sent", str(self.notifications_sent))
        stats.add_row(
            "Total Cost",
            f"${self.total_cost_usd:.4f}" if self.total_cost_usd > 0 else "$0.0000",
        )
        stats.add_row("Output File", str(self.output_file))

        self.console.print(stats)

        # Show notification criteria
        self.console.print(
            Panel(
                f"[magenta]Keywords:[/magenta] {', '.join(self.keywords)}\n"
                f"[magenta]Notifications:[/magenta] {self.notification_criteria}",
                title="Search Configuration",
            )
        )

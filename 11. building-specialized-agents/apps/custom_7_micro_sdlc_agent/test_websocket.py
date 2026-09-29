#!/usr/bin/env python3
"""
Test WebSocket connection
"""

import asyncio
import websockets
import json
from rich.console import Console

console = Console()


async def test_websocket():
    """Test WebSocket connection to the backend"""

    uri = "ws://127.0.0.1:8001/ws"

    console.print(f"[yellow]Connecting to {uri}...[/yellow]")

    try:
        async with websockets.connect(uri) as websocket:
            console.print("[green]✅ WebSocket connected successfully![/green]")

            # Listen for messages for 5 seconds
            console.print("[dim]Listening for messages (5 seconds)...[/dim]")

            try:
                async with asyncio.timeout(5):
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        console.print(f"[cyan]Received:[/cyan] {data}")
            except asyncio.TimeoutError:
                console.print("[dim]Timeout - no messages received[/dim]")

            console.print("[green]✅ WebSocket test complete![/green]")

    except Exception as e:
        console.print(f"[red]❌ WebSocket connection failed: {e}[/red]")
        console.print("[dim]Make sure the backend is running and WebSocket dependencies are installed[/dim]")
        console.print("[dim]Run: uv sync[/dim]")


if __name__ == "__main__":
    console.print("[bold]WebSocket Connection Test[/bold]\n")
    asyncio.run(test_websocket())
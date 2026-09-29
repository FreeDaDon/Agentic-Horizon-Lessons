"""
Custom Tools Module

Defines Claude Agent SDK tools for social media analysis and notifications.
Includes both analysis submission and notification capabilities.
"""

import subprocess
from typing import Dict, Any
from claude_agent_sdk import tool

# Import TTS notifier for audio fallback
from .tts_notifier import TTSNotifier

# Initialize TTS notifier (will auto-detect API key from env)
tts_notifier = TTSNotifier()


@tool(
    "submit_analysis",
    "Submit analysis results for social media content",
    {
        "summary": str,
        "sentiment": str,
        "keyword": str,
    },  # keyword that triggered the match
)
async def submit_analysis_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for Claude to submit structured analysis results.

    This ensures consistent response format for all analyzed content.

    Args:
        args: Dictionary containing:
            - summary: 1-2 sentence summary of content
            - sentiment: One of 'positive', 'negative', or 'neutral'
            - keyword: The keyword that triggered this match

    Returns:
        Dictionary with tool response content
    """

    # Validate sentiment value
    valid_sentiments = ["positive", "negative", "neutral"]
    sentiment = args.get("sentiment", "neutral").lower()

    if sentiment not in valid_sentiments:
        sentiment = "neutral"

    # Get keyword
    keyword = args.get("keyword", "unknown")

    # Return structured response with keyword and sentiment
    return {
        "content": [
            {"type": "text", "text": f"Keyword: {keyword}\nSentiment: {sentiment}"}
        ]
    }


@tool(
    "notify",
    "Send macOS notification for important social media content",
    {"title": str, "message": str, "urgency": str},  # low, normal, critical
)
async def notify_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom tool to send macOS notifications with TTS fallback.

    Uses osascript for visual alerts and optionally ElevenLabs for audio.

    Args:
        args: Dictionary containing:
            - title: Alert title
            - message: Alert message
            - urgency: One of 'low', 'normal', or 'critical'

    Returns:
        Dictionary with tool response content
    """
    try:
        title = args.get("title", "Social Hype Alert")
        message = args.get("message", "Important content detected")
        urgency = args.get("urgency", "normal")

        # Map urgency to alert button style
        if urgency == "critical":
            button_text = "Urgent!"
        elif urgency == "low":
            button_text = "Noted"
        else:
            button_text = "OK"

        # Primary notification: macOS alert dialog
        # Alerts are more visible and always appear
        script = f"""
        display alert "{title}" ¬
        message "{message}" ¬
        buttons {{"{button_text}"}} ¬
        default button 1
        """

        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=30
        )

        # Secondary notification: TTS audio (if available)
        tts_success = False
        tts_success = tts_notifier.notify(title, message)

        # Determine success message
        if result.returncode == 0:
            notification_method = "Alert shown"
            if tts_success:
                notification_method += " + TTS played"

            return {
                "content": [
                    {"type": "text", "text": f"✅ {notification_method}: {title}"}
                ]
            }
        else:
            return {
                "content": [
                    {"type": "text", "text": f"❌ Alert failed: {result.stderr}"}
                ],
                "is_error": True,
            }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Notification error: {str(e)}"}],
            "is_error": True,
        }

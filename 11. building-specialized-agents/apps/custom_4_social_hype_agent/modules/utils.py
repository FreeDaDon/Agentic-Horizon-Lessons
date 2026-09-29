"""
Utilities Module

Helper functions for the Social Hype Agent.
Includes prompt loading and configuration utilities.
"""

from pathlib import Path
from typing import NamedTuple, Dict, Any, List


class MatchedPost(NamedTuple):
    """
    Represents a matched post ready for processing.

    Attributes:
        post_data: Raw post data from WebSocket
        post_text: Extracted text content
        matched_keywords: List of keywords that matched
        match_number: Sequential match identifier
    """
    post_data: Dict[str, Any]
    post_text: str
    matched_keywords: List[str]
    match_number: int


def load_system_prompt(notification_criteria: str) -> str:
    """
    Load system prompt from external file and substitute variables.

    Args:
        notification_criteria: Custom criteria for determining notifications

    Returns:
        Formatted system prompt with substituted variables
    """
    # Get prompt file path relative to this module
    prompt_file = (
        Path(__file__).parent.parent / "prompts" / "SOCIAL_HYPE_AGENT_SYSTEM_PROMPT.md"
    )

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Substitute variables
    system_prompt = prompt_template.format(
        NOTIFICATION_CRITERIA=notification_criteria
    )

    return system_prompt


# Configuration constants
MAX_MATCHES_FOR_TESTING = 10  # Limit matches for testing purposes
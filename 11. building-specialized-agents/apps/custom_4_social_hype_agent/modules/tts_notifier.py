#!/usr/bin/env python3
"""
TTS Notifier Module

Minimal text-to-speech notification system using ElevenLabs API.
Used as audio fallback for social media alerts.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import ElevenLabs components
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play


class TTSNotifier:
    """
    Handles text-to-speech notifications using ElevenLabs API.

    Provides audio alerts for important social media content.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TTS notifier.

        Args:
            api_key: Optional ElevenLabs API key. If not provided,
                    will try to get from ELEVENLABS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.client = None
        self.enabled = False

        # Initialize client if API key is available
        if self.api_key:
            try:
                self.client = ElevenLabs(api_key=self.api_key)
                self.enabled = True
            except Exception as e:
                print(f"[yellow]⚠️  TTS initialization failed: {e}[/yellow]")
                self.enabled = False


    def speak(self, text: str, voice_id: str = "WejK3H1m7MI9CHnIjW9K") -> bool:
        """
        Convert text to speech and play audio.

        Args:
            text: Text to speak
            voice_id: ElevenLabs voice ID (defaults to a clear voice)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Generate audio using Turbo v2.5 for speed
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128"
            )

            # Play the audio
            play(audio_stream)

            return True

        except Exception as e:
            print(f"[red]❌ TTS playback failed: {e}[/red]")
            return False


    def notify(self, title: str, message: str) -> bool:
        """
        Create a spoken notification with title and message.

        Args:
            title: Notification title
            message: Notification message

        Returns:
            True if successful, False otherwise
        """
        # Combine title and message for natural speech
        speech_text = f"{title}. {message}"

        # Limit length for reasonable playback time
        if len(speech_text) > 200:
            speech_text = speech_text[:197] + "..."

        return self.speak(speech_text)


    @property
    def is_available(self) -> bool:
        """Check if TTS is available and configured."""
        return self.enabled
"""TTS backend registry and lazy loader."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import TTSBackend

BACKEND_NAMES = ["kokoro", "chatterbox", "gemini", "openai", "elevenlabs"]


def get_backend(name: str, voice: str = "", voice_ref: str = "", speed: float = 1.0) -> "TTSBackend":
    """Return an instantiated TTS backend by name."""
    if name == "kokoro":
        from .kokoro import KokoroBackend
        return KokoroBackend(voice=voice, speed=speed)
    if name == "chatterbox":
        from .chatterbox import ChatterboxBackend
        return ChatterboxBackend(voice_ref=voice_ref or None)
    if name == "gemini":
        from .gemini_tts import GeminiTTSBackend
        return GeminiTTSBackend(style_prompt=voice)
    if name == "openai":
        from .openai_tts import OpenAITTSBackend
        return OpenAITTSBackend(voice=voice or "onyx")
    if name == "elevenlabs":
        from .elevenlabs_tts import ElevenLabsTTSBackend
        return ElevenLabsTTSBackend(voice=voice or "Daniel")
    sys.exit(
        f"Unknown TTS engine '{name}'. Choose from: {', '.join(BACKEND_NAMES)}"
    )

"""OpenAI TTS backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .base import TTSBackend

DEFAULT_VOICE = "onyx"


class OpenAITTSBackend(TTSBackend):
    max_chunk_chars = 4096

    def __init__(self, voice: str = DEFAULT_VOICE):
        self._voice = voice
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            sys.exit("--engine openai requires OPENAI_API_KEY to be set.")

    @property
    def engine_name(self) -> str:
        return "openai"

    @property
    def voice_name(self) -> str:
        return self._voice

    def _synthesise_chunk(self, text: str, out_wav: Path) -> None:
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit("openai is not installed. Run: pip install -r requirements-cloud.txt")

        client = OpenAI(api_key=self._api_key)
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=self._voice,
            input=text,
            response_format="wav",
        )
        out_wav.write_bytes(response.content)

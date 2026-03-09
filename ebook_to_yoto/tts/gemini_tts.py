"""Gemini TTS backend — cloud, natural language style prompting."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from .base import TTSBackend

DEFAULT_STYLE = (
    "Speak in a warm, gentle, unhurried British voice suitable for "
    "a bedtime story for young children."
)


class GeminiTTSBackend(TTSBackend):
    max_chunk_chars = 1000

    def __init__(self, style_prompt: str = ""):
        self._style = style_prompt or DEFAULT_STYLE
        self._api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            sys.exit("--engine gemini requires GEMINI_API_KEY to be set.")

    @property
    def engine_name(self) -> str:
        return "gemini"

    @property
    def voice_name(self) -> str:
        return self._style[:60]

    def _synthesise_chunk(self, text: str, out_wav: Path) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            sys.exit(
                "google-genai is not installed. Run: pip install -r requirements-cloud.txt"
            )

        client = genai.Client(api_key=self._api_key)
        prompt = f"{self._style}\n\n{text}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                    )
                ),
            ),
        )

        audio_data = response.candidates[0].content.parts[0].inline_data.data
        # Audio comes back as WAV bytes
        out_wav.write_bytes(audio_data)

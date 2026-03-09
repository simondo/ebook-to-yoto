"""ElevenLabs TTS backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .base import TTSBackend

DEFAULT_VOICE = "Daniel"


class ElevenLabsTTSBackend(TTSBackend):
    max_chunk_chars = 2500

    def __init__(self, voice: str = DEFAULT_VOICE):
        self._voice = voice
        self._api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not self._api_key:
            sys.exit("--engine elevenlabs requires ELEVENLABS_API_KEY to be set.")

    @property
    def engine_name(self) -> str:
        return "elevenlabs"

    @property
    def voice_name(self) -> str:
        return self._voice

    def _synthesise_chunk(self, text: str, out_wav: Path) -> None:
        try:
            from elevenlabs import ElevenLabs
        except ImportError:
            sys.exit(
                "elevenlabs is not installed. Run: pip install -r requirements-cloud.txt"
            )

        client = ElevenLabs(api_key=self._api_key)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=self._voice,
            model_id="eleven_multilingual_v2",
            output_format="pcm_44100",  # raw PCM → write as WAV
        )
        # ElevenLabs PCM → WAV
        import wave, struct, io
        pcm_bytes = b"".join(audio)
        sample_rate = 44100
        n_channels = 1
        sampwidth = 2  # 16-bit

        with wave.open(str(out_wav), "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)

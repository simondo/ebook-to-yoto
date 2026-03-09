"""Kokoro TTS backend — fast, local, British voices."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Required for MPS fallback on Apple Silicon (some ops not yet implemented on MPS)
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

from .base import TTSBackend

VOICES = {
    "bf_emma": "British female (default)",
    "bm_george": "British male",
    "af_sarah": "American female",
    "am_michael": "American male",
}
DEFAULT_VOICE = "bf_emma"


class KokoroBackend(TTSBackend):
    max_chunk_chars = 500

    def __init__(self, voice: str = "", speed: float = 1.0):
        self._voice = voice or DEFAULT_VOICE
        self._speed = speed
        self._pipeline = None  # lazy load

    @property
    def engine_name(self) -> str:
        return "kokoro"

    @property
    def voice_name(self) -> str:
        return self._voice

    def _load(self):
        if self._pipeline is not None:
            return
        try:
            import torch
            from kokoro import KPipeline
        except ImportError:
            sys.exit(
                "Kokoro is not installed. Run: pip install kokoro torch torchaudio\n"
                "(or: pip install -e '.[kokoro]' from the project directory)"
            )
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        # Kokoro uses language codes; 'a' = American English, 'b' = British English
        lang = "b" if self._voice.startswith("b") else "a"
        self._pipeline = KPipeline(lang_code=lang, device=device)

    def _synthesise_chunk(self, text: str, out_wav: Path) -> None:
        import soundfile as sf
        import numpy as np

        self._load()
        audio_segments = []
        for _, _, audio in self._pipeline(text, voice=self._voice, speed=self._speed):
            if audio is not None:
                audio_segments.append(audio)

        if not audio_segments:
            # Write silence
            sf.write(str(out_wav), np.zeros(22050, dtype=np.float32), 22050)
            return

        combined = np.concatenate(audio_segments)
        sf.write(str(out_wav), combined, 24000)

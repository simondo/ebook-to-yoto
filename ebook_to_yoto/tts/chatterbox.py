"""Chatterbox TTS backend — highest quality local narration."""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Optional

from .base import TTSBackend

# Must be set before torch is imported anywhere
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")


class ChatterboxBackend(TTSBackend):
    max_chunk_chars = 250

    def __init__(self, voice_ref: Optional[str] = None):
        self._voice_ref = Path(voice_ref) if voice_ref else None
        self._model = None  # lazy load

    @property
    def engine_name(self) -> str:
        return "chatterbox"

    @property
    def voice_name(self) -> str:
        if self._voice_ref:
            return f"cloned:{self._voice_ref.stem}"
        return "chatterbox-default"

    def _load(self):
        if self._model is not None:
            return
        try:
            import torch
            from chatterbox.tts import ChatterboxTTS
        except ImportError:
            sys.exit(
                "Chatterbox is not installed. Run: pip install chatterbox-tts torch torchaudio\n"
                "(or: pip install -e '.[chatterbox]' from the project directory)"
            )

        print("Loading Chatterbox model (first run may download ~1.5 GB)...")
        try:
            model = ChatterboxTTS.from_pretrained(device="cpu")
            import torch
            if torch.backends.mps.is_available():
                model.t3 = model.t3.to("mps")
                model.s3gen = model.s3gen.to("mps")
                model.ve = model.ve.to("mps")
                model.device = "mps"
        except Exception as e:
            warnings.warn(
                f"Chatterbox model load failed ({e}). Falling back to Kokoro.",
                stacklevel=2,
            )
            raise

        self._model = model

    def _synthesise_chunk(self, text: str, out_wav: Path) -> None:
        import torchaudio

        self._load()
        kwargs: dict = {
            "exaggeration": 0.6,
            "cfg_weight": 0.5,
        }
        if self._voice_ref and self._voice_ref.exists():
            kwargs["audio_prompt_path"] = str(self._voice_ref)

        wav = self._model.generate(text, **kwargs)

        torchaudio.save(str(out_wav), wav, self._model.sr)

        # Free MPS memory between chunks
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass

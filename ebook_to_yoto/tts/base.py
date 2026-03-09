"""Abstract TTS backend with shared chunking and WAV concatenation logic."""

from __future__ import annotations

import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from ..utils import wavs_to_mp3


class TTSBackend(ABC):
    """
    Template method: subclasses implement `_synthesise_chunk` and declare
    `max_chunk_chars`. The base class handles sentence-boundary splitting,
    per-chunk synthesis, WAV concatenation, and MP3 encoding.
    """

    max_chunk_chars: int = 500  # override in subclass

    @abstractmethod
    def _synthesise_chunk(self, text: str, out_wav: Path) -> None:
        """Synthesise a single text chunk to a WAV file."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Short name for manifest and ID3 tags."""

    @property
    @abstractmethod
    def voice_name(self) -> str:
        """Voice identifier for manifest and ID3 tags."""

    # ------------------------------------------------------------------
    # Public API (called by pipeline)
    # ------------------------------------------------------------------

    def synthesise(self, text: str, out_mp3: Path) -> None:
        """
        Synthesise full chapter text to an MP3 file.
        Handles chunking, temp WAVs, ffmpeg concat + encode.
        """
        chunks = self._split_text(text)
        if not chunks:
            from ..utils import silent_mp3
            silent_mp3(out_mp3)
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            wav_paths: list[Path] = []
            for i, chunk in enumerate(chunks):
                wav_path = tmp / f"chunk_{i:04d}.wav"
                self._synthesise_chunk(chunk, wav_path)
                if wav_path.exists() and wav_path.stat().st_size > 0:
                    wav_paths.append(wav_path)

            if not wav_paths:
                from ..utils import silent_mp3
                silent_mp3(out_mp3)
                return

            wavs_to_mp3(wav_paths, out_mp3)

    # ------------------------------------------------------------------
    # Text splitting (sentence boundaries)
    # ------------------------------------------------------------------

    def _split_text(self, text: str) -> list[str]:
        """
        Split text into chunks of at most max_chunk_chars,
        breaking only at sentence boundaries.
        """
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # If a single sentence exceeds the limit, split it hard
            if len(sentence) > self.max_chunk_chars:
                if current:
                    chunks.append(current.strip())
                    current = ""
                for sub in _hard_split(sentence, self.max_chunk_chars):
                    chunks.append(sub)
                continue

            candidate = (current + " " + sentence).strip()
            if len(candidate) <= self.max_chunk_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence

        if current.strip():
            chunks.append(current.strip())

        return [c for c in chunks if c]


def _hard_split(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of max_chars at word boundaries."""
    words = text.split()
    chunks = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks

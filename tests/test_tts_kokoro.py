"""Kokoro TTS integration test — requires kokoro + torch installed."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest


@pytest.mark.slow
def test_kokoro_synthesises_wav(tmp_path):
    """10-word sentence → readable WAV with non-zero duration."""
    from ebook_to_yoto.tts.kokoro import KokoroBackend

    backend = KokoroBackend(voice="bf_emma")
    out_mp3 = tmp_path / "test_output.mp3"

    backend.synthesise("The rabbit found a golden key under the oak tree.", out_mp3)

    assert out_mp3.exists(), "MP3 file was not created"
    assert out_mp3.stat().st_size > 0, "MP3 file is empty"

    # Verify it's a readable MP3
    from mutagen.mp3 import MP3
    audio = MP3(str(out_mp3))
    assert audio.info.length > 0, "MP3 has zero duration"


@pytest.mark.slow
def test_kokoro_engine_name():
    from ebook_to_yoto.tts.kokoro import KokoroBackend
    b = KokoroBackend()
    assert b.engine_name == "kokoro"
    assert b.voice_name == "bf_emma"

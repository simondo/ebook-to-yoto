"""Shared data models for the ebook-to-yoto pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Chapter:
    """A single extracted chapter from an ebook."""
    index: int               # 1-based
    title: str
    text: str
    images: list[bytes] = field(default_factory=list)  # raw image bytes

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def estimated_minutes(self, wpm: int = 130) -> float:
        return self.word_count / wpm


@dataclass
class BookMetadata:
    title: str
    author: str = ""
    cover_bytes: Optional[bytes] = None   # JPEG/PNG bytes of cover image
    cover_ext: str = "jpg"


@dataclass
class TrackRecord:
    track: int
    title: str
    mp3: str
    icon: str
    word_count: int
    icon_source: str   # "extracted" | "generated" | "fallback"


@dataclass
class YotoManifest:
    book_title: str
    tts_engine: str
    tts_voice: str
    icon_engine: str
    generated_at: str
    tracks: list[TrackRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "book_title": self.book_title,
            "tts_engine": self.tts_engine,
            "tts_voice": self.tts_voice,
            "icon_engine": self.icon_engine,
            "generated_at": self.generated_at,
            "tracks": [
                {
                    "track": t.track,
                    "title": t.title,
                    "mp3": t.mp3,
                    "icon": t.icon,
                    "word_count": t.word_count,
                    "icon_source": t.icon_source,
                }
                for t in self.tracks
            ],
        }

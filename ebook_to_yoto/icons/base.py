"""Abstract icon generation backend."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image


class IconBackend(ABC):

    @abstractmethod
    def generate(self, prompt: str, out_path: Path) -> Path:
        """
        Generate an image from prompt, pixelate it to 16x16,
        and save as PNG at out_path. Returns out_path.
        """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Short name for manifest."""


def build_icon_prompt(chapter_text: str) -> str:
    """Build a pixel art icon prompt from chapter text."""
    prefix = (
        "pixel art icon, 16x16, children's picture book style, "
        "simple bold shapes, bright colours, plain background, no text, depicting: "
    )
    words = chapter_text.split()[:300]
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(words))
    scene = next(
        (s for s in sentences if len(s.split()) >= 4),
        sentences[0] if sentences else "a story scene",
    )
    return prefix + scene

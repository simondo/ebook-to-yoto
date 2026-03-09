"""Icon backend registry."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import IconBackend

BACKEND_NAMES = ["stable-diffusion", "gemini", "openai"]


def get_backend(name: str) -> "IconBackend":
    if name == "stable-diffusion":
        from .stable_diffusion import StableDiffusionBackend
        return StableDiffusionBackend()
    if name == "gemini":
        from .gemini import GeminiIconBackend
        return GeminiIconBackend()
    if name == "openai":
        from .openai_img import OpenAIIconBackend
        return OpenAIIconBackend()
    sys.exit(
        f"Unknown icon engine '{name}'. Choose from: {', '.join(BACKEND_NAMES)}"
    )

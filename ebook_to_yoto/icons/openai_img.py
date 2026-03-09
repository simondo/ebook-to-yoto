"""OpenAI DALL-E 3 icon backend."""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from PIL import Image

from .base import IconBackend
from .pixelate import pixelate


class OpenAIIconBackend(IconBackend):

    def __init__(self):
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            sys.exit("--icon-engine openai requires OPENAI_API_KEY to be set.")

    @property
    def engine_name(self) -> str:
        return "openai"

    def generate(self, prompt: str, out_path: Path) -> Path:
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit(
                "openai is not installed. Run: pip install -r requirements-cloud.txt"
            )
        import urllib.request

        client = OpenAI(api_key=self._api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        with urllib.request.urlopen(image_url) as resp:
            image_bytes = resp.read()

        with Image.open(io.BytesIO(image_bytes)) as im:
            result = pixelate(im)
        result.save(str(out_path), "PNG")
        return out_path

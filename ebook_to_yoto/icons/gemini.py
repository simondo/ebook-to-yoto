"""Gemini / Imagen 3 icon backend."""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from PIL import Image

from .base import IconBackend
from .pixelate import pixelate


class GeminiIconBackend(IconBackend):

    def __init__(self):
        self._api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            sys.exit("--icon-engine gemini requires GEMINI_API_KEY to be set.")

    @property
    def engine_name(self) -> str:
        return "gemini"

    def generate(self, prompt: str, out_path: Path) -> Path:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            sys.exit(
                "google-genai is not installed. Run: pip install -r requirements-cloud.txt"
            )

        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
        image_bytes = response.generated_images[0].image.image_bytes
        with Image.open(io.BytesIO(image_bytes)) as im:
            result = pixelate(im)
        result.save(str(out_path), "PNG")
        return out_path

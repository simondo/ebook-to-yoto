"""Local image generation backend using mflux (FLUX.1-schnell via MLX)."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

from PIL import Image

from .base import IconBackend
from .pixelate import pixelate


class StableDiffusionBackend(IconBackend):

    @property
    def engine_name(self) -> str:
        return "stable-diffusion"

    def generate(self, prompt: str, out_path: Path) -> Path:
        try:
            return self._generate_mflux(prompt, out_path)
        except Exception as e:
            warnings.warn(
                f"mflux image generation failed ({e}). Will use bundled fallback icon.",
                stacklevel=2,
            )
            raise

    def _generate_mflux(self, prompt: str, out_path: Path) -> Path:
        try:
            from mflux.models.flux.variants.txt2img.flux import Flux1
            from mflux.models.common.config.model_config import ModelConfig
        except ImportError:
            sys.exit(
                "mflux is not installed.\n"
                "Run: pip install mflux\n"
                "(or: pip install -e '.[local]' from the project directory)"
            )

        import os
        if not os.environ.get("HF_TOKEN"):
            print(
                "  Note: FLUX.1-schnell requires a free HuggingFace account.\n"
                "  First run: accept terms at https://huggingface.co/black-forest-labs/FLUX.1-schnell\n"
                "  Then set: export HF_TOKEN=your_token_from_https://huggingface.co/settings/tokens\n"
                "  (Will use bundled fallback icons until HF_TOKEN is set.)"
            )

        print("  Generating icon with FLUX.1-schnell (first run downloads ~6 GB)...")

        flux = Flux1(
            model_config=ModelConfig.schnell(),
            quantize=8,  # 8-bit — good quality/size tradeoff (~6 GB)
        )

        result = flux.generate_image(
            seed=42,
            prompt=prompt,
            num_inference_steps=2,  # schnell works well at 2–4 steps
            height=512,
            width=512,
            guidance=0.0,  # schnell is guidance-distilled
        )

        # GeneratedImage has a .image property (PIL Image)
        pil_image = result.image

        pixelated = pixelate(pil_image)
        pixelated.save(str(out_path), "PNG")
        return out_path

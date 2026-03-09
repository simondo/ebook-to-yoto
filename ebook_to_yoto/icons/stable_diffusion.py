"""Local Stable Diffusion icon backend via MLX."""

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
            return self._generate_mlx(prompt, out_path)
        except Exception as e:
            warnings.warn(
                f"Stable Diffusion generation failed ({e}). "
                "Will use bundled fallback icon.",
                stacklevel=2,
            )
            raise

    def _generate_mlx(self, prompt: str, out_path: Path) -> Path:
        try:
            from mlx_stablediffusion import StableDiffusionPipeline
        except ImportError:
            try:
                # Alternative package name
                import mlx_stable_diffusion as mlx_sd
                StableDiffusionPipeline = mlx_sd.StableDiffusionPipeline
            except ImportError:
                sys.exit(
                    "mlx-stablediffusion is not installed.\n"
                    "Run: pip install mlx-stablediffusion\n"
                    "(or: pip install -e '.[local]' from the project directory)"
                )

        print("  Generating icon with Stable Diffusion (first run downloads ~2.5 GB)...")
        pipe = StableDiffusionPipeline.from_pretrained(
            "stabilityai/sdxl-turbo",
            cache_dir=str(Path.home() / ".cache" / "mlx-sd"),
        )
        images = pipe(
            prompt,
            num_inference_steps=1,
            height=512,
            width=512,
            guidance_scale=0.0,  # SDXL-Turbo uses no guidance
        )
        pil_image = images[0] if isinstance(images, list) else images

        result = pixelate(pil_image)
        result.save(str(out_path), "PNG")
        return out_path

"""Shared pixelation logic: any image → 16×16 RGBA PNG."""

from __future__ import annotations

from pathlib import Path
from PIL import Image


def pixelate(source_image: Image.Image) -> Image.Image:
    """
    Convert any PIL image to a Yoto-compatible 16×16 pixel art icon.
    - Resize to 64×64 (LANCZOS)
    - Quantise to 16 colours
    - Remap near-black pixels (R+G+B < 30) to dark navy (10, 10, 40)
    - Resize to 16×16 (NEAREST)
    """
    img = source_image.convert("RGBA")
    img = img.resize((64, 64), Image.LANCZOS)

    # Quantise to 16 colours (FASTOCTREE is required for RGBA images)
    quantised = img.quantize(colors=16, method=Image.Quantize.FASTOCTREE)
    img = quantised.convert("RGBA")

    # Remap near-black pixels (invisible on Yoto display)
    pixels = img.load()
    for y in range(64):
        for x in range(64):
            r, g, b, a = pixels[x, y]
            if r + g + b < 30:
                pixels[x, y] = (10, 10, 40, a)

    img = img.resize((16, 16), Image.NEAREST)
    return img


def pixelate_file(src: Path, dst: Path) -> None:
    """Load an image file, pixelate it, and save as PNG at dst."""
    with Image.open(src) as im:
        result = pixelate(im)
    result.save(str(dst), "PNG")


def pixelate_bytes(image_bytes: bytes, dst: Path) -> None:
    """Pixelate raw image bytes and save as PNG at dst."""
    import io
    with Image.open(io.BytesIO(image_bytes)) as im:
        result = pixelate(im)
    result.save(str(dst), "PNG")

"""Extract embedded images from ebook chapters."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image
import io

from .pixelate import pixelate


def extract_chapter_icon(image_bytes_list: list[bytes], out_path: Path) -> bool:
    """
    Try to extract the first usable image from a list of raw image byte strings.
    Pixelates and saves as PNG at out_path.
    Returns True if successful, False if no usable image found.
    """
    for raw in image_bytes_list:
        if not raw:
            continue
        try:
            with Image.open(io.BytesIO(raw)) as im:
                result = pixelate(im)
            result.save(str(out_path), "PNG")
            return True
        except Exception:
            continue
    return False

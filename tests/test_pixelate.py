"""Tests for the pixelation pipeline."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from ebook_to_yoto.icons.pixelate import pixelate, pixelate_bytes


def make_test_image(width=256, height=256, color=(200, 100, 50, 255)) -> Image.Image:
    img = Image.new("RGBA", (width, height), color)
    return img


class TestPixelate:
    def test_output_is_16x16(self):
        img = make_test_image()
        result = pixelate(img)
        assert result.size == (16, 16)

    def test_output_is_rgba(self):
        img = make_test_image()
        result = pixelate(img)
        assert result.mode == "RGBA"

    def test_no_pure_black_pixels(self):
        # Create an image with pure black pixels
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
        result = pixelate(img)
        pixels = list(result.getdata())
        for r, g, b, a in pixels:
            assert r + g + b >= 30, f"Found near-black pixel: ({r},{g},{b},{a})"

    def test_near_black_remapped_to_navy(self):
        img = Image.new("RGBA", (64, 64), (5, 5, 5, 255))
        result = pixelate(img)
        pixels = list(result.getdata())
        for r, g, b, a in pixels:
            if r + g + b < 30:
                pytest.fail(f"Near-black pixel not remapped: ({r},{g},{b})")

    def test_colour_palette_limited(self):
        # After quantisation, palette should be ≤16 colours
        img = make_test_image()
        result = pixelate(img)
        unique_colours = len(set(result.getdata()))
        assert unique_colours <= 16, f"Too many colours: {unique_colours}"

    def test_large_input_works(self):
        img = make_test_image(1024, 1024)
        result = pixelate(img)
        assert result.size == (16, 16)

    def test_pixelate_bytes(self, tmp_path):
        img = make_test_image()
        buf = io.BytesIO()
        img.save(buf, "PNG")
        out = tmp_path / "icon.png"
        pixelate_bytes(buf.getvalue(), out)
        assert out.exists()
        with Image.open(out) as loaded:
            assert loaded.size == (16, 16)

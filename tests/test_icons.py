"""Tests for icon backends: fallback, prompt builder, chapter extractor."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from ebook_to_yoto.icons.fallback import (
    ICONS,
    ensure_bundled_icons,
    get_fallback_icon,
)
from ebook_to_yoto.icons.base import build_icon_prompt
from ebook_to_yoto.icons.extractor import extract_chapter_icon


# ---------------------------------------------------------------------------
# Fallback icons
# ---------------------------------------------------------------------------

class TestFallbackIcons:
    def test_ensure_bundled_icons_returns_correct_count(self, tmp_path, monkeypatch):
        import ebook_to_yoto.icons.fallback as fb
        monkeypatch.setattr(fb, "BUNDLED_DIR", tmp_path / "icons")
        paths = fb.ensure_bundled_icons()
        assert len(paths) == len(ICONS)

    def test_all_icons_are_valid_16x16_png(self, tmp_path, monkeypatch):
        import ebook_to_yoto.icons.fallback as fb
        monkeypatch.setattr(fb, "BUNDLED_DIR", tmp_path / "icons")
        paths = fb.ensure_bundled_icons()
        for p in paths:
            assert p.exists(), f"Missing icon: {p}"
            with Image.open(p) as img:
                assert img.size == (16, 16), f"{p.name}: expected 16×16, got {img.size}"
                assert img.format == "PNG" or p.suffix == ".png"

    def test_icons_are_rgba(self, tmp_path, monkeypatch):
        import ebook_to_yoto.icons.fallback as fb
        monkeypatch.setattr(fb, "BUNDLED_DIR", tmp_path / "icons")
        paths = fb.ensure_bundled_icons()
        for p in paths:
            with Image.open(p) as img:
                assert img.mode == "RGBA", f"{p.name}: expected RGBA, got {img.mode}"

    def test_ensure_bundled_icons_idempotent(self, tmp_path, monkeypatch):
        """Calling twice doesn't regenerate (files already exist)."""
        import ebook_to_yoto.icons.fallback as fb
        monkeypatch.setattr(fb, "BUNDLED_DIR", tmp_path / "icons")
        paths1 = fb.ensure_bundled_icons()
        mtimes1 = [p.stat().st_mtime for p in paths1]
        paths2 = fb.ensure_bundled_icons()
        mtimes2 = [p.stat().st_mtime for p in paths2]
        assert mtimes1 == mtimes2

    def test_get_fallback_icon_wraps_around(self, tmp_path, monkeypatch):
        """Index beyond count wraps around (modulo)."""
        import ebook_to_yoto.icons.fallback as fb
        monkeypatch.setattr(fb, "BUNDLED_DIR", tmp_path / "icons")
        n = len(ICONS)
        p0 = fb.get_fallback_icon(0)
        pn = fb.get_fallback_icon(n)
        assert p0 == pn

    def test_get_fallback_icon_different_per_index(self, tmp_path, monkeypatch):
        import ebook_to_yoto.icons.fallback as fb
        monkeypatch.setattr(fb, "BUNDLED_DIR", tmp_path / "icons")
        icons = [fb.get_fallback_icon(i) for i in range(len(ICONS))]
        assert len(set(icons)) == len(ICONS), "Each index should return a distinct icon"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

class TestBuildIconPrompt:
    def test_prompt_contains_pixel_art_prefix(self):
        prompt = build_icon_prompt("Once upon a time there was a dragon.")
        assert "pixel art" in prompt.lower()
        assert "16x16" in prompt

    def test_prompt_includes_text_content(self):
        prompt = build_icon_prompt("The brave knight rode through the forest.")
        assert "knight" in prompt or "forest" in prompt or "rode" in prompt

    def test_prompt_with_empty_text_uses_fallback(self):
        prompt = build_icon_prompt("")
        assert "pixel art" in prompt.lower()
        assert len(prompt) > 20  # something sensible produced

    def test_prompt_truncates_very_long_text(self):
        long_text = "word " * 5000
        prompt = build_icon_prompt(long_text)
        # Should not be absurdly long (uses only first 300 words)
        assert len(prompt) < 2000

    def test_prompt_picks_first_meaningful_sentence(self):
        text = "Short. The old wizard cast a powerful spell in the crumbling tower."
        prompt = build_icon_prompt(text)
        # The second sentence has ≥4 words so should be chosen
        assert "wizard" in prompt or "spell" in prompt


# ---------------------------------------------------------------------------
# Chapter icon extractor
# ---------------------------------------------------------------------------

def _make_png_bytes(width=64, height=64, colour=(200, 100, 50)) -> bytes:
    """Create a small valid PNG in memory."""
    img = Image.new("RGB", (width, height), colour)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


class TestExtractChapterIcon:
    def test_extracts_first_valid_image(self, tmp_path):
        out = tmp_path / "icon.png"
        raw = _make_png_bytes()
        result = extract_chapter_icon([raw], out)
        assert result is True
        assert out.exists()
        with Image.open(out) as img:
            assert img.size == (16, 16)

    def test_returns_false_for_empty_list(self, tmp_path):
        out = tmp_path / "icon.png"
        result = extract_chapter_icon([], out)
        assert result is False
        assert not out.exists()

    def test_skips_invalid_bytes_tries_next(self, tmp_path):
        out = tmp_path / "icon.png"
        bad = b"\x00\x01\x02NOTANIMAGE"
        good = _make_png_bytes()
        result = extract_chapter_icon([bad, good], out)
        assert result is True
        assert out.exists()

    def test_returns_false_when_all_invalid(self, tmp_path):
        out = tmp_path / "icon.png"
        result = extract_chapter_icon([b"bad", b"data"], out)
        assert result is False

    def test_returns_false_for_empty_bytes(self, tmp_path):
        out = tmp_path / "icon.png"
        result = extract_chapter_icon([b""], out)
        assert result is False

    def test_output_is_rgba_png(self, tmp_path):
        out = tmp_path / "icon.png"
        extract_chapter_icon([_make_png_bytes()], out)
        with Image.open(out) as img:
            assert img.mode == "RGBA"

    def test_handles_jpeg_input(self, tmp_path):
        out = tmp_path / "icon.png"
        img = Image.new("RGB", (100, 100), (60, 120, 200))
        buf = io.BytesIO()
        img.save(buf, "JPEG")
        result = extract_chapter_icon([buf.getvalue()], out)
        assert result is True
        with Image.open(out) as o:
            assert o.size == (16, 16)

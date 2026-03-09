"""
Bundled fallback icons — 12 pre-made 16×16 pixel art PNGs.
Generated programmatically with Pillow. Each icon is a simple geometric design.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

BUNDLED_DIR = Path(__file__).parent.parent.parent / "bundled_icons"

# (name, background_colour, draw_function_name)
ICONS = [
    "book", "star", "moon", "sun", "tree",
    "house", "cat", "rabbit", "dragon", "crown", "ship", "flower",
]


def _make_book() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (30, 80, 180, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 13, 13], fill=(240, 220, 160, 255))
    d.rectangle([2, 2, 3, 13], fill=(200, 60, 60, 255))
    d.line([2, 7, 13, 7], fill=(180, 160, 100, 255), width=1)
    return img


def _make_star() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (20, 20, 60, 255))
    d = ImageDraw.Draw(img)
    pts = [8, 1, 10, 6, 15, 6, 11, 10, 13, 15, 8, 12, 3, 15, 5, 10, 1, 6, 6, 6]
    d.polygon(pts, fill=(255, 220, 40, 255))
    return img


def _make_moon() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (10, 10, 40, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 13, 13], fill=(240, 230, 120, 255))
    d.ellipse([5, 1, 15, 11], fill=(10, 10, 40, 255))
    return img


def _make_sun() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (30, 120, 200, 255))
    d = ImageDraw.Draw(img)
    # Rays
    for x, y, x2, y2 in [(8, 0, 8, 2), (8, 13, 8, 15), (0, 7, 2, 7), (13, 7, 15, 7),
                          (2, 2, 3, 3), (12, 2, 13, 3), (2, 12, 3, 13), (12, 12, 13, 13)]:
        d.line([x, y, x2, y2], fill=(255, 230, 50, 255), width=1)
    d.ellipse([4, 4, 11, 11], fill=(255, 210, 30, 255))
    return img


def _make_tree() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (80, 180, 80, 255))
    d = ImageDraw.Draw(img)
    d.polygon([8, 1, 2, 8, 5, 8, 1, 14, 14, 14, 11, 8, 14, 8], fill=(30, 120, 30, 255))
    d.rectangle([7, 11, 9, 15], fill=(140, 90, 40, 255))
    return img


def _make_house() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (100, 180, 220, 255))
    d = ImageDraw.Draw(img)
    d.polygon([8, 1, 1, 7, 15, 7], fill=(220, 60, 40, 255))
    d.rectangle([2, 7, 13, 14], fill=(240, 220, 180, 255))
    d.rectangle([6, 10, 9, 14], fill=(140, 100, 60, 255))
    d.rectangle([3, 9, 5, 12], fill=(180, 220, 255, 255))
    return img


def _make_cat() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (60, 60, 60, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([3, 5, 12, 13], fill=(200, 180, 160, 255))
    d.polygon([3, 5, 1, 1, 5, 4], fill=(200, 180, 160, 255))
    d.polygon([12, 5, 14, 1, 10, 4], fill=(200, 180, 160, 255))
    d.ellipse([5, 7, 7, 9], fill=(80, 60, 80, 255))
    d.ellipse([9, 7, 11, 9], fill=(80, 60, 80, 255))
    d.point([7, 11], fill=(200, 100, 100, 255))
    return img


def _make_rabbit() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (100, 180, 100, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 6, 11, 13], fill=(240, 240, 240, 255))
    d.ellipse([5, 1, 7, 7], fill=(240, 240, 240, 255))
    d.ellipse([9, 1, 11, 7], fill=(240, 240, 240, 255))
    d.ellipse([6, 8, 8, 10], fill=(200, 150, 150, 255))
    d.ellipse([8, 8, 10, 10], fill=(200, 150, 150, 255))
    return img


def _make_dragon() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (20, 20, 20, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 11, 10], fill=(40, 160, 40, 255))
    d.polygon([11, 5, 15, 3, 13, 8], fill=(200, 80, 20, 255))
    d.ellipse([5, 5, 7, 7], fill=(255, 200, 40, 255))
    d.polygon([4, 10, 2, 14, 6, 12, 8, 15, 10, 12, 13, 14, 11, 10], fill=(40, 140, 40, 255))
    return img


def _make_crown() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (20, 20, 80, 255))
    d = ImageDraw.Draw(img)
    d.polygon([1, 12, 1, 5, 5, 8, 8, 2, 11, 8, 15, 5, 15, 12], fill=(220, 180, 20, 255))
    d.rectangle([1, 11, 15, 13], fill=(220, 180, 20, 255))
    d.ellipse([7, 1, 9, 3], fill=(200, 50, 50, 255))
    return img


def _make_ship() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (60, 140, 200, 255))
    d = ImageDraw.Draw(img)
    d.polygon([1, 10, 3, 13, 13, 13, 15, 10], fill=(180, 120, 60, 255))
    d.rectangle([7, 3, 8, 10], fill=(180, 120, 60, 255))
    d.polygon([8, 3, 8, 9, 13, 6], fill=(240, 60, 60, 255))
    d.line([1, 12, 15, 12], fill=(60, 120, 200, 255), width=1)
    return img


def _make_flower() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (100, 200, 100, 255))
    d = ImageDraw.Draw(img)
    for cx, cy in [(8, 4), (8, 12), (4, 8), (12, 8), (5, 5), (11, 5), (5, 11), (11, 11)]:
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(240, 120, 180, 255))
    d.ellipse([5, 5, 10, 10], fill=(255, 220, 40, 255))
    d.rectangle([7, 10, 8, 15], fill=(40, 160, 40, 255))
    return img


_GENERATORS = {
    "book": _make_book, "star": _make_star, "moon": _make_moon, "sun": _make_sun,
    "tree": _make_tree, "house": _make_house, "cat": _make_cat, "rabbit": _make_rabbit,
    "dragon": _make_dragon, "crown": _make_crown, "ship": _make_ship, "flower": _make_flower,
}


def ensure_bundled_icons() -> list[Path]:
    """Generate all bundled icons if they don't exist. Returns list of paths."""
    BUNDLED_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in ICONS:
        path = BUNDLED_DIR / f"{name}.png"
        if not path.exists():
            img = _GENERATORS[name]()
            img.save(str(path), "PNG")
        paths.append(path)
    return paths


def get_fallback_icon(track_index: int) -> Path:
    """Return the fallback icon path for the given (0-based) track index."""
    paths = ensure_bundled_icons()
    return paths[track_index % len(paths)]

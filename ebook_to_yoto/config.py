"""Configuration loading: CLI flags > per-book sidecar > user config > defaults."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Python 3.11+ has tomllib in stdlib
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

CONFIG_DIR = Path.home() / ".config" / "ebook-to-yoto"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG_TEMPLATE = """\
[tts]
engine = "chatterbox"         # kokoro | chatterbox | gemini | openai | elevenlabs
voice = ""                    # leave blank to use engine default
voice_ref = ""                # path to WAV for Chatterbox voice cloning (optional)
speed = 1.0

[icons]
engine = "stable-diffusion"   # stable-diffusion | gemini | openai
no_icons = false

[output]
split_cards = false
skip_existing = false
"""


@dataclass
class TTSConfig:
    engine: str = "chatterbox"
    voice: str = ""
    voice_ref: str = ""
    speed: float = 1.0


@dataclass
class IconsConfig:
    engine: str = "stable-diffusion"
    no_icons: bool = False


@dataclass
class OutputConfig:
    split_cards: bool = False
    skip_existing: bool = False


@dataclass
class Config:
    tts: TTSConfig = field(default_factory=TTSConfig)
    icons: IconsConfig = field(default_factory=IconsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(ebook_path: Optional[Path] = None) -> Config:
    """
    Load config in priority order (lowest to highest):
      1. Hardcoded defaults
      2. User config file (~/.config/ebook-to-yoto/config.toml)
      3. Per-book sidecar (<book>.yoto.toml)

    CLI flags are applied on top by the caller.
    Creates the user config file with defaults on first run.
    """
    config = Config()

    # Ensure user config exists
    if not CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(DEFAULT_CONFIG_TEMPLATE)
        print(f"Created default config at {CONFIG_PATH}")

    # Load user config
    _apply_toml_file(config, CONFIG_PATH, source="user config")

    # Load per-book sidecar
    if ebook_path is not None:
        sidecar = ebook_path.with_suffix(".yoto.toml")
        if sidecar.exists():
            print(f"Using per-book settings from {sidecar.name}")
            _apply_toml_file(config, sidecar, source=sidecar.name)

    return config


def _apply_toml_file(config: Config, path: Path, source: str) -> None:
    """Parse a TOML file and apply its values onto config, ignoring unknown keys."""
    if tomllib is None:
        print(
            "Warning: tomllib/tomli not available — cannot read config files. "
            "Run: pip install tomli",
            file=sys.stderr,
        )
        return

    try:
        data = tomllib.loads(path.read_text())
    except Exception as e:
        print(f"Warning: Could not parse {source}: {e}", file=sys.stderr)
        return

    tts_data = data.get("tts", {})
    for key, val in tts_data.items():
        if hasattr(config.tts, key):
            setattr(config.tts, key, val)
        else:
            print(f"Warning: Unknown key '{key}' in [tts] of {source}, ignoring.")

    icons_data = data.get("icons", {})
    for key, val in icons_data.items():
        if hasattr(config.icons, key):
            setattr(config.icons, key, val)
        else:
            print(f"Warning: Unknown key '{key}' in [icons] of {source}, ignoring.")

    output_data = data.get("output", {})
    for key, val in output_data.items():
        if hasattr(config.output, key):
            setattr(config.output, key, val)
        else:
            print(f"Warning: Unknown key '{key}' in [output] of {source}, ignoring.")

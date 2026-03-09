"""Click CLI entry point for ebook-to-yoto."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from .config import load_config
from .tts import BACKEND_NAMES as TTS_BACKENDS
from .icons import BACKEND_NAMES as ICON_BACKENDS


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("ebook_file", type=click.Path(exists=True, path_type=Path))
# TTS options
@click.option(
    "--engine", "-e",
    type=click.Choice(TTS_BACKENDS),
    default=None,
    help="TTS engine  [default: chatterbox]",
)
@click.option("--voice", default=None, help="Voice name (default per engine)")
@click.option(
    "--voice-ref",
    type=click.Path(path_type=Path),
    default=None,
    help="WAV reference for voice cloning (chatterbox only, ≥6s)",
)
@click.option("--speed", type=float, default=None, help="Speaking speed multiplier  [default: 1.0]")
@click.option(
    "--list-voices",
    is_flag=True,
    default=False,
    help="Print available voices for the selected engine and exit",
)
# Icon options
@click.option(
    "--icon-engine",
    type=click.Choice(ICON_BACKENDS),
    default=None,
    help="Icon generation backend  [default: stable-diffusion]",
)
@click.option("--no-icons", is_flag=True, default=False, help="Skip icon generation entirely")
# Output options
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output folder  [default: <bookname>_yoto/]",
)
@click.option(
    "--split-cards",
    is_flag=True,
    default=False,
    help="Split output into multiple card folders if over Yoto limits",
)
@click.option(
    "--skip-existing",
    is_flag=True,
    default=False,
    help="Skip tracks whose MP3 already exists (resume a run)",
)
# Utility
@click.option(
    "--scan",
    is_flag=True,
    default=False,
    help="Print chapter list and resolved settings; write no files",
)
def main(
    ebook_file: Path,
    engine: Optional[str],
    voice: Optional[str],
    voice_ref: Optional[Path],
    speed: Optional[float],
    list_voices: bool,
    icon_engine: Optional[str],
    no_icons: bool,
    output_dir: Optional[Path],
    split_cards: bool,
    skip_existing: bool,
    scan: bool,
) -> None:
    """Convert a DRM-free ebook into Yoto-ready MP3s and pixel art icons.

    EBOOK_FILE: Path to .epub, .pdf, .mobi, or .txt
    """
    from .utils import check_ffmpeg

    # Load config (creates default on first run, loads sidecar if present)
    config = load_config(ebook_file)

    # Apply CLI overrides (CLI flags > sidecar > config file > defaults)
    if engine:
        config.tts.engine = engine
    if voice:
        config.tts.voice = voice
    if voice_ref:
        config.tts.voice_ref = str(voice_ref)
    if speed is not None:
        config.tts.speed = speed
    if icon_engine:
        config.icons.engine = icon_engine
    if no_icons:
        config.icons.no_icons = True
    if split_cards:
        config.output.split_cards = True
    if skip_existing:
        config.output.skip_existing = True

    if list_voices:
        _print_voices(config.tts.engine)
        return

    if scan:
        _print_scan(ebook_file, config)
        return

    check_ffmpeg()

    from .pipeline import run
    run(
        ebook_path=ebook_file,
        output_dir=output_dir,
        config=config,
        tts_engine_name=config.tts.engine,
        icon_engine_name=config.icons.engine,
        voice=config.tts.voice,
        voice_ref=config.tts.voice_ref,
        speed=config.tts.speed,
        no_icons=config.icons.no_icons,
        skip_existing=config.output.skip_existing,
        split_cards=config.output.split_cards,
        scan_only=False,
    )


def _print_scan(ebook_file: Path, config) -> None:
    """Print chapter list and resolved settings without processing."""
    print(f"Settings for: {ebook_file.name}")
    print(f"  TTS engine:  {config.tts.engine}")
    print(f"  Voice:       {config.tts.voice or '(engine default)'}")
    print(f"  Speed:       {config.tts.speed}")
    print(f"  Icon engine: {config.icons.engine}")
    print(f"  No icons:    {config.icons.no_icons}")
    print()

    from .pipeline import run
    run(
        ebook_path=ebook_file,
        output_dir=None,
        config=config,
        tts_engine_name=config.tts.engine,
        icon_engine_name=config.icons.engine,
        voice=config.tts.voice,
        voice_ref=config.tts.voice_ref,
        speed=config.tts.speed,
        no_icons=config.icons.no_icons,
        skip_existing=False,
        split_cards=False,
        scan_only=True,
    )


def _print_voices(engine: str) -> None:
    if engine == "kokoro":
        from .tts.kokoro import VOICES
        print("Kokoro voices:")
        for v, desc in VOICES.items():
            print(f"  {v:<15} {desc}")
    elif engine == "chatterbox":
        print("Chatterbox uses its own default voice or a --voice-ref WAV for cloning.")
    elif engine == "openai":
        print("OpenAI voices: alloy, echo, fable, onyx (default), nova, shimmer")
    elif engine == "elevenlabs":
        print(
            "ElevenLabs: use a voice name or voice ID from https://elevenlabs.io/voice-library\n"
            "Default: Daniel (British male)\n"
            "Tip: search 'Scottish' at elevenlabs.io/voice-library for Scottish accent voices."
        )
    elif engine == "gemini":
        print(
            "Gemini TTS: use --voice as a free-text style description.\n"
            "Example: --voice 'slow and warm, like a British grandmother telling a bedtime story'"
        )

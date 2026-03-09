"""Filename sanitisation, word count, and shared helpers."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a safe filename slug."""
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:max_len]


def track_filename(index: int, title: str) -> str:
    """Return e.g. '01_Once-Upon-a-Time' (no extension)."""
    return f"{index:02d}_{slugify(title)}"


def check_ffmpeg() -> None:
    """Exit with a clear message if ffmpeg is not on PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except FileNotFoundError:
        sys.exit("ffmpeg is required. Run: brew install ffmpeg")


def check_ebook_convert() -> None:
    """Exit with a clear message if ebook-convert (Calibre) is not on PATH."""
    try:
        subprocess.run(
            ["ebook-convert", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except FileNotFoundError:
        sys.exit(
            "MOBI support requires Calibre. Run: brew install --cask calibre\n"
            "Then restart your terminal so 'ebook-convert' is on PATH."
        )


def wavs_to_mp3(wav_paths: list[Path], out_mp3: Path) -> None:
    """Concatenate one or more WAV files and encode to 128kbps MP3 via ffmpeg."""
    check_ffmpeg()
    if len(wav_paths) == 1:
        cmd = [
            "ffmpeg", "-y", "-i", str(wav_paths[0]),
            "-b:a", "128k", "-f", "mp3", str(out_mp3),
        ]
    else:
        # Write a concat list file
        concat_file = out_mp3.with_suffix(".concat.txt")
        concat_file.write_text(
            "\n".join(f"file '{p.resolve()}'" for p in wav_paths)
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-b:a", "128k", "-f", "mp3", str(out_mp3),
        ]

    result = subprocess.run(cmd, capture_output=True)
    if len(wav_paths) > 1:
        concat_file.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed encoding {out_mp3.name}:\n{result.stderr.decode()}"
        )


def silent_mp3(out_mp3: Path, duration_s: float = 1.0) -> None:
    """Write a silent MP3 placeholder of the given duration."""
    check_ffmpeg()
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
        "-t", str(duration_s),
        "-b:a", "128k", "-f", "mp3", str(out_mp3),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

"""MP3 tagging, Yoto limit checks, and manifest writing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from mutagen.id3 import ID3, TIT2, TRCK, TALB, TPE1, ID3NoHeaderError, APIC
from mutagen.mp3 import MP3

from .models import YotoManifest

# Yoto hard limits
YOTO_MAX_TRACKS = 100
YOTO_MAX_TRACK_SIZE_MB = 100
YOTO_MAX_TRACK_DURATION_MIN = 60
YOTO_MAX_TOTAL_SIZE_MB = 500
YOTO_MAX_TOTAL_DURATION_HRS = 5


def tag_mp3(
    mp3_path: Path,
    title: str,
    track_num: int,
    album: str,
    artist: str,
    cover_bytes: Optional[bytes] = None,
    cover_mime: str = "image/jpeg",
) -> None:
    """Write ID3v2.3 tags to an MP3 file."""
    try:
        tags = ID3(str(mp3_path))
    except ID3NoHeaderError:
        tags = ID3()

    tags["TIT2"] = TIT2(encoding=3, text=title)
    tags["TRCK"] = TRCK(encoding=3, text=str(track_num))
    tags["TALB"] = TALB(encoding=3, text=album)
    tags["TPE1"] = TPE1(encoding=3, text=artist)

    if cover_bytes:
        tags["APIC"] = APIC(
            encoding=3,
            mime=cover_mime,
            type=3,  # Cover (front)
            desc="Cover",
            data=cover_bytes,
        )

    tags.save(str(mp3_path), v2_version=3)


def check_yoto_limits(output_dir: Path, track_count: int) -> list[str]:
    """
    Check Yoto hard limits on the output directory.
    Returns a list of warning strings (empty = all good).
    """
    warnings = []

    if track_count > YOTO_MAX_TRACKS:
        warnings.append(
            f"Track count ({track_count}) exceeds Yoto limit of {YOTO_MAX_TRACKS}. "
            "Use --split-cards to create multiple card folders."
        )

    mp3_files = sorted(output_dir.glob("*.mp3"))
    total_size_bytes = 0
    total_duration_s = 0.0

    for mp3_path in mp3_files:
        size_mb = mp3_path.stat().st_size / (1024 * 1024)
        total_size_bytes += mp3_path.stat().st_size

        try:
            audio = MP3(str(mp3_path))
            duration_s = audio.info.length
            total_duration_s += duration_s
            if duration_s > YOTO_MAX_TRACK_DURATION_MIN * 60:
                warnings.append(
                    f"Track '{mp3_path.name}' is {duration_s/60:.1f} min, "
                    f"exceeds Yoto per-track limit of {YOTO_MAX_TRACK_DURATION_MIN} min."
                )
        except Exception:
            pass

        if size_mb > YOTO_MAX_TRACK_SIZE_MB:
            warnings.append(
                f"Track '{mp3_path.name}' is {size_mb:.1f} MB, "
                f"exceeds Yoto per-track limit of {YOTO_MAX_TRACK_SIZE_MB} MB."
            )

    total_size_mb = total_size_bytes / (1024 * 1024)
    total_duration_hrs = total_duration_s / 3600

    if total_size_mb > YOTO_MAX_TOTAL_SIZE_MB:
        warnings.append(
            f"Total size {total_size_mb:.1f} MB exceeds Yoto limit of {YOTO_MAX_TOTAL_SIZE_MB} MB."
        )
    if total_duration_hrs > YOTO_MAX_TOTAL_DURATION_HRS:
        warnings.append(
            f"Total duration {total_duration_hrs:.1f} hrs exceeds Yoto limit of {YOTO_MAX_TOTAL_DURATION_HRS} hrs."
        )

    return warnings


def write_manifest(manifest: YotoManifest, output_dir: Path) -> None:
    """Write manifest.json to the output directory."""
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False))


def verify_outputs(output_dir: Path, expected_mp3s: list[str]) -> list[str]:
    """Verify each expected MP3 exists, is non-zero, and is readable. Returns error messages."""
    errors = []
    for filename in expected_mp3s:
        path = output_dir / filename
        if not path.exists():
            errors.append(f"Missing output: {filename}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"Zero-byte output: {filename}")
            continue
        try:
            MP3(str(path))
        except Exception as e:
            errors.append(f"Unreadable MP3 {filename}: {e}")
    return errors

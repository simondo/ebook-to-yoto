"""Main pipeline orchestrator."""

from __future__ import annotations

import shutil
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .config import Config
from .extractor import extract
from .models import BookMetadata, Chapter, TrackRecord, YotoManifest
from .postprocess import check_yoto_limits, tag_mp3, verify_outputs, write_manifest
from .utils import silent_mp3, slugify, track_filename

YOTO_MAX_TRACKS = 100
WORDS_PER_MINUTE = 130  # approximate narration speed


def run(
    ebook_path: Path,
    output_dir: Optional[Path],
    config: Config,
    tts_engine_name: str,
    icon_engine_name: str,
    voice: str = "",
    voice_ref: str = "",
    speed: float = 1.0,
    no_icons: bool = False,
    skip_existing: bool = False,
    split_cards: bool = False,
    scan_only: bool = False,
) -> None:
    """Full pipeline: extract → preflight → per-chapter TTS + icons → postprocess."""

    # ------------------------------------------------------------------ #
    # Step 1: Extract
    # ------------------------------------------------------------------ #
    print(f"Reading {ebook_path.name}...")
    meta, chapters = extract(ebook_path)

    if not chapters:
        sys.exit("No chapters found in this ebook.")

    print(f"  Title:    {meta.title}")
    print(f"  Chapters: {len(chapters)}")
    total_words = sum(c.word_count for c in chapters)
    est_mins = total_words / WORDS_PER_MINUTE / speed
    print(f"  Words:    {total_words:,}  (~{est_mins:.0f} min at {speed}x speed)")

    if scan_only:
        print("\nChapter list:")
        for ch in chapters:
            est = ch.word_count / WORDS_PER_MINUTE / speed
            print(f"  {ch.index:3d}. {ch.title}  ({ch.word_count} words, ~{est:.1f} min)")
        return

    # ------------------------------------------------------------------ #
    # Step 2: Preflight checks
    # ------------------------------------------------------------------ #
    if len(chapters) > YOTO_MAX_TRACKS and not split_cards:
        print(
            f"\nWarning: Book has {len(chapters)} chapters. Yoto cards hold {YOTO_MAX_TRACKS} max.\n"
            f"Processing first {YOTO_MAX_TRACKS} chapters. Use --split-cards to process all."
        )
        chapters = chapters[:YOTO_MAX_TRACKS]

    for ch in chapters:
        est = ch.word_count / WORDS_PER_MINUTE / speed
        if est > 60:
            print(f"Warning: '{ch.title}' is ~{est:.0f} min — exceeds Yoto 60-min track limit.")

    # ------------------------------------------------------------------ #
    # Step 3: Set up output directory
    # ------------------------------------------------------------------ #
    if split_cards and len(chapters) > YOTO_MAX_TRACKS:
        # Split into card sub-folders
        card_groups = [
            chapters[i:i + YOTO_MAX_TRACKS]
            for i in range(0, len(chapters), YOTO_MAX_TRACKS)
        ]
    else:
        card_groups = [chapters]

    base_dir = output_dir or Path(f"{slugify(meta.title)}_yoto")

    for card_idx, card_chapters in enumerate(card_groups):
        if len(card_groups) > 1:
            card_dir = base_dir / f"card_{card_idx + 1}"
        else:
            card_dir = base_dir
        card_dir.mkdir(parents=True, exist_ok=True)

        _process_card(
            chapters=card_chapters,
            meta=meta,
            card_dir=card_dir,
            config=config,
            tts_engine_name=tts_engine_name,
            icon_engine_name=icon_engine_name,
            voice=voice,
            voice_ref=voice_ref,
            speed=speed,
            no_icons=no_icons,
            skip_existing=skip_existing,
        )

    print(f"\nDone! Output: {base_dir.resolve()}")
    print("Upload files to: https://my.yotoplay.com/make-your-own")


def _process_card(
    chapters: list[Chapter],
    meta: BookMetadata,
    card_dir: Path,
    config: Config,
    tts_engine_name: str,
    icon_engine_name: str,
    voice: str,
    voice_ref: str,
    speed: float,
    no_icons: bool,
    skip_existing: bool,
) -> None:
    # Lazy-load backends
    from .tts import get_backend as get_tts
    tts = get_tts(tts_engine_name, voice=voice, voice_ref=voice_ref, speed=speed)

    icon_backend = None
    if not no_icons:
        from .icons import get_backend as get_icon
        icon_backend = get_icon(icon_engine_name)

    from .icons.extractor import extract_chapter_icon
    from .icons.fallback import get_fallback_icon
    from .icons.base import build_icon_prompt

    track_records: list[TrackRecord] = []
    expected_mp3s: list[str] = []

    print(f"\nProcessing {len(chapters)} chapters → {card_dir}")

    for ch in tqdm(chapters, desc="Chapters", unit="ch"):
        base = track_filename(ch.index, ch.title)
        mp3_name = base + ".mp3"
        icon_name = base + "_icon.png"
        mp3_path = card_dir / mp3_name
        icon_path = card_dir / icon_name
        expected_mp3s.append(mp3_name)
        icon_source = "fallback"

        # -- TTS --
        if skip_existing and mp3_path.exists() and mp3_path.stat().st_size > 0:
            tqdm.write(f"  Skipping existing: {mp3_name}")
        else:
            try:
                tts.synthesise(ch.text, mp3_path)
                tag_mp3(
                    mp3_path,
                    title=ch.title,
                    track_num=ch.index,
                    album=meta.title,
                    artist=tts.voice_name,
                    cover_bytes=meta.cover_bytes,
                    cover_mime=f"image/{meta.cover_ext}",
                )
            except Exception as e:
                tqdm.write(f"  Error synthesising '{ch.title}': {e}. Writing silent placeholder.")
                silent_mp3(mp3_path)

        # -- Icons --
        if not no_icons and not (skip_existing and icon_path.exists()):
            # A: Try extracting from chapter images
            if ch.images and extract_chapter_icon(ch.images, icon_path):
                icon_source = "extracted"
            else:
                # B: Generate via backend
                if icon_backend is not None:
                    try:
                        prompt = build_icon_prompt(ch.text)
                        icon_backend.generate(prompt, icon_path)
                        icon_source = "generated"
                    except Exception as e:
                        tqdm.write(f"  Icon generation failed for '{ch.title}': {e}. Using fallback.")
                        _copy_fallback(ch.index - 1, icon_path)
                else:
                    _copy_fallback(ch.index - 1, icon_path)
        elif no_icons:
            icon_name = ""
            icon_source = "none"

        track_records.append(TrackRecord(
            track=ch.index,
            title=ch.title,
            mp3=mp3_name,
            icon=icon_name,
            word_count=ch.word_count,
            icon_source=icon_source,
        ))

    # -- Cover image --
    if meta.cover_bytes:
        cover_path = card_dir / f"cover.{meta.cover_ext}"
        cover_path.write_bytes(meta.cover_bytes)

    # -- Manifest --
    manifest = YotoManifest(
        book_title=meta.title,
        tts_engine=tts.engine_name,
        tts_voice=tts.voice_name,
        icon_engine=icon_backend.engine_name if icon_backend else "none",
        generated_at=datetime.now().isoformat(timespec="seconds"),
        tracks=track_records,
    )
    write_manifest(manifest, card_dir)

    # -- Post-checks --
    errors = verify_outputs(card_dir, expected_mp3s)
    for err in errors:
        print(f"  Output error: {err}")

    warnings_list = check_yoto_limits(card_dir, len(chapters))
    for w in warnings_list:
        print(f"  Yoto limit warning: {w}")

    # -- Summary --
    total_size = sum((card_dir / f).stat().st_size for f in expected_mp3s if (card_dir / f).exists())
    print(f"  Tracks: {len(chapters)}")
    print(f"  Size:   {total_size / (1024*1024):.1f} MB")


def _copy_fallback(track_index: int, icon_path: Path) -> None:
    from .icons.fallback import get_fallback_icon
    fallback = get_fallback_icon(track_index)
    shutil.copy2(fallback, icon_path)

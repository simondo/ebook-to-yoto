"""Format detection, text + image extraction from ebooks."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from .models import BookMetadata, Chapter
from .utils import check_ebook_convert

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".epub", ".pdf", ".mobi", ".txt"}


def extract(path: Path) -> tuple[BookMetadata, list[Chapter]]:
    """
    Extract BookMetadata and ordered list of Chapters from an ebook file.
    Raises SystemExit with a clear message on unsupported format or read error.
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        sys.exit(
            f"Unsupported format '{ext}'. Supported: "
            + ", ".join(sorted(SUPPORTED_EXTENSIONS))
        )
    if not path.exists():
        sys.exit(f"File not found: {path}")

    if ext == ".mobi":
        return _extract_mobi(path)
    if ext == ".epub":
        return _extract_epub(path)
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext == ".txt":
        return _extract_txt(path)

    sys.exit(f"Unhandled format: {ext}")  # unreachable


# ---------------------------------------------------------------------------
# EPUB
# ---------------------------------------------------------------------------

def _extract_epub(path: Path) -> tuple[BookMetadata, list[Chapter]]:
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
        import warnings
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    except ImportError:
        sys.exit("Missing dependency: pip install ebooklib beautifulsoup4 lxml")

    book = epub.read_epub(str(path), options={"ignore_ncx": True})

    # Metadata
    title = _first(book.get_metadata("DC", "title")) or path.stem
    author = _first(book.get_metadata("DC", "creator")) or ""
    cover_bytes, cover_ext = _epub_cover(book)
    meta = BookMetadata(title=title, author=author, cover_bytes=cover_bytes, cover_ext=cover_ext)

    # Spine items
    chapters: list[Chapter] = []
    seen_texts: list[str] = []
    idx = 1

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "lxml")
        text = _soup_to_text(soup)

        if len(text.split()) < 50:
            continue

        # Near-duplicate detection (>95% word overlap with previous chapter)
        if seen_texts and _overlap(text, seen_texts[-1]) > 0.95:
            # Keep the longer one
            if len(text) > len(seen_texts[-1]) and chapters:
                chapters[-1] = Chapter(
                    index=chapters[-1].index,
                    title=chapters[-1].title,
                    text=text,
                    images=_epub_chapter_images(book, item, soup),
                )
                seen_texts[-1] = text
            continue

        title_tag = soup.find(re.compile(r"^h[1-3]$"))
        chapter_title = title_tag.get_text(strip=True) if title_tag else f"Chapter {idx}"

        images = _epub_chapter_images(book, item, soup)
        chapters.append(Chapter(index=idx, title=chapter_title, text=text, images=images))
        seen_texts.append(text)
        idx += 1

    return meta, chapters


def _epub_cover(book) -> tuple[Optional[bytes], str]:
    """Try to extract cover image from EPUB metadata."""
    try:
        from ebooklib import epub
        # Method 1: OPF cover meta item
        cover_id = None
        for meta in book.get_metadata("OPF", "cover"):
            cover_id = meta[1].get("content")
            break
        if cover_id:
            item = book.get_item_with_id(cover_id)
            if item:
                ext = Path(item.file_name).suffix.lstrip(".") or "jpg"
                return item.get_content(), ext
        # Method 2: first image item that looks like a cover
        from ebooklib import epub as ebooklib_epub
        import ebooklib
        for item in book.get_items_of_type(ebooklib.ITEM_COVER):
            ext = Path(item.file_name).suffix.lstrip(".") or "jpg"
            return item.get_content(), ext
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            name = item.file_name.lower()
            if "cover" in name:
                ext = Path(item.file_name).suffix.lstrip(".") or "jpg"
                return item.get_content(), ext
    except Exception:
        pass
    return None, "jpg"


def _epub_chapter_images(book, item, soup) -> list[bytes]:
    """Extract image bytes referenced in this EPUB chapter item."""
    images = []
    try:
        import ebooklib
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src", "")
            if not src:
                continue
            # Resolve relative path from item
            item_dir = str(Path(item.file_name).parent)
            rel = src.lstrip("../")
            for img_item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if img_item.file_name.endswith(rel) or rel in img_item.file_name:
                    images.append(img_item.get_content())
                    break
    except Exception:
        pass
    return images


def _soup_to_text(soup) -> str:
    """Extract clean text from BeautifulSoup, preserving paragraph breaks."""
    for tag in soup(["script", "style", "head"]):
        tag.decompose()
    paragraphs = []
    for elem in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        t = elem.get_text(separator=" ", strip=True)
        if t:
            paragraphs.append(t)
    if not paragraphs:
        return soup.get_text(separator=" ", strip=True)
    return "\n\n".join(paragraphs)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

WORDS_PER_CHUNK = 1500


def _extract_pdf(path: Path) -> tuple[BookMetadata, list[Chapter]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Missing dependency: pip install pypdf")

    reader = PdfReader(str(path))
    title = path.stem
    try:
        info = reader.metadata
        if info and info.title:
            title = info.title
    except Exception:
        pass

    meta = BookMetadata(title=title)

    # Extract text page by page, then group into ~1500-word chunks
    pages_text: list[str] = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            pages_text.append("")

    chapters = _chunk_text_to_chapters(pages_text, WORDS_PER_CHUNK)
    return meta, chapters


# ---------------------------------------------------------------------------
# TXT
# ---------------------------------------------------------------------------

def _extract_txt(path: Path) -> tuple[BookMetadata, list[Chapter]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = BookMetadata(title=path.stem)

    # Split on double newlines (paragraph breaks)
    raw_chunks = re.split(r"\n{2,}", text)
    # Group into ~1500-word chunks
    chapters = _chunk_text_to_chapters(raw_chunks, WORDS_PER_CHUNK)
    return meta, chapters


# ---------------------------------------------------------------------------
# MOBI — convert via Calibre, then process as EPUB
# ---------------------------------------------------------------------------

def _extract_mobi(path: Path) -> tuple[BookMetadata, list[Chapter]]:
    check_ebook_convert()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_epub = Path(tmpdir) / (path.stem + ".epub")
        result = subprocess.run(
            ["ebook-convert", str(path), str(out_epub)],
            capture_output=True,
        )
        if result.returncode != 0 or not out_epub.exists():
            sys.exit(
                f"ebook-convert failed for {path.name}:\n"
                + result.stderr.decode(errors="replace")
            )
        return _extract_epub(out_epub)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _chunk_text_to_chapters(text_blocks: list[str], target_words: int) -> list[Chapter]:
    """Group text blocks into chapters of approximately target_words words."""
    chapters: list[Chapter] = []
    current_words: list[str] = []
    idx = 1

    for block in text_blocks:
        words = block.split()
        if not words:
            continue
        current_words.extend(words)
        if len(current_words) >= target_words:
            chapter_text = " ".join(current_words)
            chapters.append(Chapter(index=idx, title=f"Chapter {idx}", text=chapter_text))
            idx += 1
            current_words = []

    # Remaining text
    if current_words:
        chapter_text = " ".join(current_words)
        if chapters:
            # Append to last chapter if it's very short
            if len(current_words) < target_words // 3:
                last = chapters[-1]
                chapters[-1] = Chapter(
                    index=last.index,
                    title=last.title,
                    text=last.text + " " + chapter_text,
                    images=last.images,
                )
            else:
                chapters.append(Chapter(index=idx, title=f"Chapter {idx}", text=chapter_text))
        else:
            chapters.append(Chapter(index=idx, title=f"Chapter {idx}", text=chapter_text))

    return chapters


def _overlap(text_a: str, text_b: str) -> float:
    """Return Jaccard word overlap between two texts (0.0–1.0)."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _first(metadata_list) -> Optional[str]:
    """Extract the string value from the first ebooklib metadata entry."""
    if not metadata_list:
        return None
    first = metadata_list[0]
    if isinstance(first, tuple):
        return first[0] if first[0] else None
    return str(first) if first else None

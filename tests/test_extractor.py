"""Tests for text extraction from ebook formats."""

from __future__ import annotations

from pathlib import Path

import pytest

from ebook_to_yoto.extractor import extract, _overlap, _chunk_text_to_chapters


class TestEpubExtraction:
    def test_extracts_three_chapters(self, test_epub):
        meta, chapters = extract(test_epub)
        assert len(chapters) == 3

    def test_chapter_titles(self, test_epub):
        _, chapters = extract(test_epub)
        titles = [c.title for c in chapters]
        assert "Chapter One" in titles
        assert "Chapter Two" in titles
        assert "Chapter Three" in titles

    def test_chapter_indices_are_sequential(self, test_epub):
        _, chapters = extract(test_epub)
        assert [c.index for c in chapters] == [1, 2, 3]

    def test_book_title(self, test_epub):
        meta, _ = extract(test_epub)
        assert meta.title == "The Test Book"

    def test_chapter_has_text(self, test_epub):
        _, chapters = extract(test_epub)
        for ch in chapters:
            assert len(ch.text) > 10
            assert ch.word_count > 5

    def test_no_duplicate_chapters(self, test_epub):
        _, chapters = extract(test_epub)
        texts = [c.text for c in chapters]
        for i, t in enumerate(texts):
            for j, t2 in enumerate(texts):
                if i != j:
                    assert _overlap(t, t2) < 0.95


class TestTxtExtraction:
    def test_extracts_chunks(self, test_txt):
        meta, chapters = extract(test_txt)
        assert len(chapters) >= 1

    def test_meta_title_from_filename(self, test_txt):
        meta, _ = extract(test_txt)
        assert meta.title == "test_book"

    def test_text_content(self, test_txt):
        _, chapters = extract(test_txt)
        combined = " ".join(c.text for c in chapters)
        assert "fox" in combined.lower()


class TestPdfExtraction:
    def test_unsupported_extension(self, tmp_path):
        bad = tmp_path / "book.xyz"
        bad.write_text("hello")
        with pytest.raises(SystemExit):
            extract(bad)

    def test_missing_file(self, tmp_path):
        with pytest.raises(SystemExit):
            extract(tmp_path / "nonexistent.epub")


class TestHelpers:
    def test_overlap_identical(self):
        text = "the quick brown fox jumps over the lazy dog"
        assert _overlap(text, text) == 1.0

    def test_overlap_disjoint(self):
        assert _overlap("apple orange banana", "cat dog mouse") == 0.0

    def test_overlap_partial(self):
        score = _overlap("apple orange banana", "apple grape mango")
        assert 0.0 < score < 1.0

    def test_chunk_groups_into_chapters(self):
        blocks = ["word " * 200] * 10  # 10 blocks of 200 words each
        chapters = _chunk_text_to_chapters(blocks, target_words=500)
        assert len(chapters) >= 2
        for ch in chapters:
            assert ch.word_count > 0

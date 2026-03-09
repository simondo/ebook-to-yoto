"""Tests for the CLI interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ebook_to_yoto.cli import main


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "EBOOK_FILE" in result.output

    def test_scan_prints_chapters(self, test_epub):
        runner = CliRunner()
        result = runner.invoke(main, [str(test_epub), "--scan"])
        assert result.exit_code == 0
        assert "Chapter" in result.output
        assert "Chapter One" in result.output

    def test_scan_writes_no_files(self, test_epub, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, [str(test_epub), "--scan"])
        # No MP3 or PNG files should be created
        mp3_files = list(tmp_path.rglob("*.mp3"))
        assert mp3_files == [], f"Unexpected MP3 files: {mp3_files}"

    def test_scan_chapter_count(self, test_epub):
        runner = CliRunner()
        result = runner.invoke(main, [str(test_epub), "--scan"])
        assert result.exit_code == 0
        # Our test EPUB has 3 chapters
        assert result.output.count("Chapter") >= 3

    def test_list_voices_kokoro(self, test_epub):
        runner = CliRunner()
        result = runner.invoke(main, [str(test_epub), "--engine", "kokoro", "--list-voices"])
        assert result.exit_code == 0
        assert "bf_emma" in result.output

    def test_list_voices_elevenlabs(self, test_epub):
        runner = CliRunner()
        result = runner.invoke(main, [str(test_epub), "--engine", "elevenlabs", "--list-voices"])
        assert result.exit_code == 0
        assert "Daniel" in result.output

    def test_invalid_engine(self, test_epub):
        runner = CliRunner()
        result = runner.invoke(main, [str(test_epub), "--engine", "fakeengine"])
        assert result.exit_code != 0

    def test_missing_file(self):
        runner = CliRunner()
        result = runner.invoke(main, ["nonexistent_book.epub"])
        assert result.exit_code != 0

"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def test_epub(fixtures_dir, tmp_path_factory) -> Path:
    """Return path to a minimal synthetic test EPUB, generating it if needed."""
    path = fixtures_dir / "test_book.epub"
    if not path.exists():
        from tests.fixtures.make_fixtures import make_epub
        make_epub(path)
    return path


@pytest.fixture(scope="session")
def test_txt(fixtures_dir) -> Path:
    path = fixtures_dir / "test_book.txt"
    if not path.exists():
        from tests.fixtures.make_fixtures import make_txt
        make_txt(path)
    return path

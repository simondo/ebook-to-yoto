"""Tests for config loading: defaults, TOML parsing, sidecar, unknown keys."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from ebook_to_yoto.config import Config, _apply_toml_file, load_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_toml(tmp_path: Path, content: str, name: str = "config.toml") -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def test_default_config_values():
    cfg = Config()
    assert cfg.tts.engine == "chatterbox"
    assert cfg.tts.speed == 1.0
    assert cfg.tts.voice == ""
    assert cfg.tts.voice_ref == ""
    assert cfg.icons.engine == "stable-diffusion"
    assert cfg.icons.no_icons is False
    assert cfg.output.split_cards is False
    assert cfg.output.skip_existing is False


# ---------------------------------------------------------------------------
# _apply_toml_file
# ---------------------------------------------------------------------------

def test_apply_toml_overrides_tts(tmp_path):
    p = write_toml(tmp_path, """
        [tts]
        engine = "kokoro"
        speed = 1.5
    """)
    cfg = Config()
    _apply_toml_file(cfg, p, source="test")
    assert cfg.tts.engine == "kokoro"
    assert cfg.tts.speed == 1.5
    # untouched keys stay at default
    assert cfg.tts.voice == ""


def test_apply_toml_overrides_icons_and_output(tmp_path):
    p = write_toml(tmp_path, """
        [icons]
        no_icons = true

        [output]
        skip_existing = true
        split_cards = true
    """)
    cfg = Config()
    _apply_toml_file(cfg, p, source="test")
    assert cfg.icons.no_icons is True
    assert cfg.output.skip_existing is True
    assert cfg.output.split_cards is True


def test_apply_toml_unknown_keys_ignored(tmp_path, capsys):
    """Unknown TOML keys produce a warning but do not raise."""
    p = write_toml(tmp_path, """
        [tts]
        engine = "kokoro"
        nonexistent_key = "hello"
    """)
    cfg = Config()
    _apply_toml_file(cfg, p, source="myconfig")
    assert cfg.tts.engine == "kokoro"
    out = capsys.readouterr().out
    assert "nonexistent_key" in out
    assert "ignoring" in out.lower()


def test_apply_toml_invalid_file_does_not_raise(tmp_path, capsys):
    """A malformed TOML file prints a warning and leaves config unchanged."""
    p = write_toml(tmp_path, "this is not toml ][[[")
    cfg = Config()
    _apply_toml_file(cfg, p, source="bad.toml")
    assert cfg.tts.engine == "chatterbox"  # unchanged default
    err = capsys.readouterr().err
    assert "Warning" in err


def test_apply_toml_partial_section(tmp_path):
    """Only [tts] section present — [icons] and [output] stay at defaults."""
    p = write_toml(tmp_path, """
        [tts]
        engine = "openai"
    """)
    cfg = Config()
    _apply_toml_file(cfg, p, source="test")
    assert cfg.tts.engine == "openai"
    assert cfg.icons.engine == "stable-diffusion"
    assert cfg.output.split_cards is False


# ---------------------------------------------------------------------------
# load_config — first-run creates default file
# ---------------------------------------------------------------------------

def test_load_config_creates_default_on_first_run(tmp_path, monkeypatch):
    """load_config creates ~/.config/ebook-to-yoto/config.toml if absent."""
    import ebook_to_yoto.config as cfg_mod
    fake_dir = tmp_path / ".config" / "ebook-to-yoto"
    fake_path = fake_dir / "config.toml"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_PATH", fake_path)

    assert not fake_path.exists()
    cfg = load_config()
    assert fake_path.exists()
    assert "[tts]" in fake_path.read_text()
    # Defaults still intact
    assert cfg.tts.engine == "chatterbox"


def test_load_config_reads_existing_user_config(tmp_path, monkeypatch):
    import ebook_to_yoto.config as cfg_mod
    fake_dir = tmp_path / ".config" / "ebook-to-yoto"
    fake_dir.mkdir(parents=True)
    fake_path = fake_dir / "config.toml"
    fake_path.write_text('[tts]\nengine = "kokoro"\n')
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_PATH", fake_path)

    cfg = load_config()
    assert cfg.tts.engine == "kokoro"


# ---------------------------------------------------------------------------
# Sidecar
# ---------------------------------------------------------------------------

def test_load_config_reads_sidecar(tmp_path, monkeypatch):
    """Per-book .yoto.toml is applied on top of user config."""
    import ebook_to_yoto.config as cfg_mod
    fake_dir = tmp_path / ".config" / "ebook-to-yoto"
    fake_dir.mkdir(parents=True)
    fake_path = fake_dir / "config.toml"
    fake_path.write_text('[tts]\nengine = "kokoro"\n')
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_PATH", fake_path)

    ebook = tmp_path / "mybook.epub"
    ebook.touch()
    sidecar = tmp_path / "mybook.yoto.toml"
    sidecar.write_text('[tts]\nengine = "openai"\nspeed = 1.2\n')

    cfg = load_config(ebook)
    assert cfg.tts.engine == "openai"   # sidecar wins
    assert cfg.tts.speed == 1.2


def test_load_config_no_sidecar(tmp_path, monkeypatch):
    """No sidecar present — user config is used."""
    import ebook_to_yoto.config as cfg_mod
    fake_dir = tmp_path / ".config" / "ebook-to-yoto"
    fake_dir.mkdir(parents=True)
    fake_path = fake_dir / "config.toml"
    fake_path.write_text('[tts]\nengine = "elevenlabs"\n')
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_PATH", fake_path)

    ebook = tmp_path / "mybook.epub"
    ebook.touch()

    cfg = load_config(ebook)
    assert cfg.tts.engine == "elevenlabs"

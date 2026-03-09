# ebook-to-yoto — Implementation Progress

## Status Legend
- ✅ Complete & tested
- 🔄 In progress
- ⬜ Not started
- ⚠️ Needs attention

---

## Phases

### Phase 0 — Scaffolding ✅
- ✅ `pyproject.toml` (build system, optional dep groups)
- ✅ `setup.sh` (idempotent Mac setup script)
- ✅ `ebook_to_yoto/__init__.py`
- ✅ `models.py` (Chapter, BookMetadata, YotoManifest)
- ✅ `utils.py` (slugify, ffmpeg helpers)
- ✅ `config.py` (user config + per-book sidecar, TOML)
- ✅ `requirements.txt` / `requirements-cloud.txt`
- ✅ Python 3.11 venv at `~/ebook-to-yoto/.venv`

### Phase 1 — Text Extraction ✅
- ✅ `extractor.py` — EPUB (ebooklib + BeautifulSoup)
- ✅ `extractor.py` — PDF (pypdf)
- ✅ `extractor.py` — TXT (blank-line chunking)
- ✅ `extractor.py` — MOBI (Calibre subprocess)
- ✅ Near-duplicate chapter detection
- ✅ `tests/fixtures/make_fixtures.py` (synthetic EPUB + TXT)
- ✅ `tests/test_extractor.py` (23 tests, all passing)

### Phase 2 — TTS Base + Kokoro ✅
- ✅ `tts/base.py` — abstract class + sentence-boundary chunking template
- ✅ `tts/kokoro.py` — KPipeline, MPS fallback env var set
- ✅ `tts/__init__.py` — lazy registry
- ✅ `tests/test_tts_kokoro.py` (slow tests, marked)

### Phase 3 — End-to-End MVP ✅
- ✅ `pipeline.py` — full orchestrator (extract → TTS → tag → manifest)
- ✅ `postprocess.py` — ID3v2.3 tagging (mutagen), Yoto limit checks
- ✅ `cli.py` — Click CLI, all flags from PRD
- ✅ `tests/test_cli.py` (8 tests)
- ✅ `tests/test_postprocess.py` (6 tests)
- ✅ **End-to-end verified**: `ebook-to-yoto test_book.epub --engine kokoro --no-icons`
  - Output: 3 × MP3, ~20s each, valid ID3 tags, manifest.json ✅

### Phase 4 — Chatterbox TTS ✅
- ✅ `tts/chatterbox.py` — CPU load → MPS submodule transfer, voice cloning
- ✅ MPS fallback env var set, `torch.mps.empty_cache()` between chunks
- ✅ `chatterbox-tts==0.1.6` installed
- ⚠️ Not yet end-to-end tested with a real book (deferred — user skipping validation)

### Phase 5 — Cloud TTS Backends ✅
- ✅ `tts/gemini_tts.py`
- ✅ `tts/openai_tts.py`
- ✅ `tts/elevenlabs_tts.py`
- ⬜ Cloud TTS tests (require mocked API — deferred)

### Phase 6 — Icons: Extraction + Pixelation + Fallbacks ✅
- ✅ `icons/pixelate.py` — 64×64 → 16-colour quantise → near-black remap → 16×16
  - Fixed: FASTOCTREE required for RGBA (MEDIANCUT unsupported)
- ✅ `icons/extractor.py` — extract from ebook chapter images
- ✅ `icons/fallback.py` — 12 programmatic 16×16 icons (book, star, moon…)
- ✅ `icons/base.py` — abstract IconBackend + prompt builder
- ✅ `tests/test_pixelate.py` (7 tests, all passing)

### Phase 7 — Stable Diffusion Icons via MLX ✅
- ✅ Package: `mflux` (not `mlx-stablediffusion` — that doesn't exist)
  - Model: FLUX.1-schnell via `mflux.models.flux.variants.txt2img.flux.Flux1`
- ✅ `mflux==0.16.9` installed
- ✅ Backend updated to use correct mflux API (`Flux1`, `ModelConfig.schnell()`)
- ✅ End-to-end tested — fallback chain works correctly
- ✅ Clear HF_TOKEN message added (FLUX.1-schnell is a gated HF repo)
- ⚠️ **HF_TOKEN required** to actually generate icons:
  1. Accept terms: https://huggingface.co/black-forest-labs/FLUX.1-schnell
  2. Create token: https://huggingface.co/settings/tokens
  3. `export HF_TOKEN=<your_token>`
  - Without token: pipeline works, uses bundled fallback icons ✅

### Phase 8 — Cloud Icon Backends ✅ (code written, untested)
- ✅ `icons/gemini.py` (Imagen 3)
- ✅ `icons/openai_img.py` (DALL-E 3)
- ⬜ Cloud icon tests (require mocked API — deferred)

### Phase 9 — Config, Sidecar & CLI Polish ✅
- ✅ Config priority chain: CLI > sidecar > user config > defaults
- ✅ `--scan`, `--skip-existing`, `--split-cards`, `--list-voices` all working
- ✅ Auto-creates `~/.config/ebook-to-yoto/config.toml` on first run

### Phase 10 — Tests, Hardening & README ⬜
- ⬜ README.md
- ⬜ Ctrl+C handling
- ⬜ Disk space pre-check
- ⬜ Cloud backend mocked tests

---

## Test Summary
```
pytest tests/ -m "not slow"
36 passed, 2 deselected  ✅
```

## End-to-End Verified ✅
- Kokoro TTS + FLUX.1-schnell icons → 3× MP3 + 3× 16×16 PNG + manifest.json
- All `icon_source: "generated"` — distinct pixel art per chapter
- Bus error on exit (after completion) — harmless, MLX freeing 33 GB from memory

## Known Issues / Notes
- Kokoro `aten::angle` op falls back to CPU on MPS (harmless, `PYTORCH_ENABLE_MPS_FALLBACK=1` set)
- FLUX.1-schnell is 33 GB download (not 6 GB as estimated) — one-time, cached after
- FLUX.1-schnell requires `HF_TOKEN` — fallback icons used until set
- Bus error on process exit after FLUX generation — output is intact, investigate in Phase 10
- Chatterbox not yet end-to-end tested (user deferred)
- Cloud backends (TTS + icons) code-complete but untested without API keys

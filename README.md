# ebook-to-yoto

Convert DRM-free ebooks (EPUB, PDF, MOBI, TXT) into Yoto-ready MP3 audio tracks and 16×16 pixel art icons — entirely on your Mac.

## Requirements

- macOS (Apple Silicon M1/M2/M3 recommended)
- Python 3.11
- [ffmpeg](https://ffmpeg.org/) — `brew install ffmpeg`

## Installation

```bash
# Clone and set up
git clone <repo> ebook-to-yoto
cd ebook-to-yoto

# Create venv and install
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Optional dependencies

| Feature | Command |
|---|---|
| Kokoro TTS (fast local) | `pip install -e '.[kokoro]'` |
| Chatterbox TTS (high quality local) | `pip install -e '.[chatterbox]'` |
| FLUX.1-schnell icons (local) | `pip install -e '.[local]'` |
| Cloud TTS + icons | `pip install -e '.[cloud]'` |
| All of the above | `pip install -e '.[kokoro,chatterbox,local,cloud]'` |

## Quick start

```bash
source .venv/bin/activate

# Convert an ebook with Kokoro TTS (no icon generation)
ebook-to-yoto my_book.epub --engine kokoro --no-icons

# Full pipeline with Chatterbox TTS + FLUX icons
ebook-to-yoto my_book.epub --engine chatterbox

# Preview chapters without generating any files
ebook-to-yoto my_book.epub --scan
```

Then upload the output folder to [my.yotoplay.com/make-your-own](https://my.yotoplay.com/make-your-own).

## TTS engines

| Engine | Flag | Quality | Speed | Requires |
|---|---|---|---|---|
| **chatterbox** | `--engine chatterbox` | ★★★★★ | ~45s/ch | Local (GPU) |
| **kokoro** | `--engine kokoro` | ★★★★ | ~5s/ch | Local |
| **openai** | `--engine openai` | ★★★★ | Fast | `OPENAI_API_KEY` |
| **elevenlabs** | `--engine elevenlabs` | ★★★★★ | Fast | `ELEVENLABS_API_KEY` |
| **gemini** | `--engine gemini` | ★★★★ | Fast | `GEMINI_API_KEY` |

### Voice options

```bash
# List available voices for an engine
ebook-to-yoto my_book.epub --engine kokoro --list-voices

# Specify a voice
ebook-to-yoto my_book.epub --engine kokoro --voice af_bella

# Voice cloning with Chatterbox (provide a ≥6s reference WAV)
ebook-to-yoto my_book.epub --engine chatterbox --voice-ref my_voice.wav
```

## Icon generation

| Engine | Flag | Quality | Requires |
|---|---|---|---|
| **stable-diffusion** | `--icon-engine stable-diffusion` | ★★★★★ | `HF_TOKEN`, ~33 GB download |
| **openai** | `--icon-engine openai` | ★★★★ | `OPENAI_API_KEY` |
| **gemini** | `--icon-engine gemini` | ★★★★ | `GEMINI_API_KEY` |
| *(fallback)* | `--no-icons` + automatic | ★★★ | None |

### FLUX.1-schnell setup (local icons)

FLUX.1-schnell is a gated HuggingFace model. One-time setup:

1. Accept terms at [huggingface.co/black-forest-labs/FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
2. Create a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. `export HF_TOKEN=<your_token>`

First run downloads ~33 GB (cached afterward).

Without `HF_TOKEN`, the pipeline still works and uses bundled pixel art fallback icons.

## All CLI flags

```
Usage: ebook-to-yoto [OPTIONS] EBOOK_FILE

  Convert a DRM-free ebook into Yoto-ready MP3s and pixel art icons.

Options:
  -e, --engine [chatterbox|kokoro|gemini|openai|elevenlabs]
                                  TTS engine  [default: chatterbox]
  --voice TEXT                    Voice name (default per engine)
  --voice-ref PATH                WAV reference for voice cloning (chatterbox only, ≥6s)
  --speed FLOAT                   Speaking speed multiplier  [default: 1.0]
  --list-voices                   Print available voices for the engine and exit
  --icon-engine [stable-diffusion|gemini|openai]
                                  Icon generation backend  [default: stable-diffusion]
  --no-icons                      Skip icon generation entirely
  -o, --output-dir PATH           Output folder  [default: <bookname>_yoto/]
  --split-cards                   Split into multiple card folders if over Yoto limits
  --skip-existing                 Skip tracks whose MP3 already exists (resume a run)
  --scan                          Print chapter list and resolved settings; write no files
  -h, --help                      Show this message and exit.
```

## Configuration

Settings are loaded in priority order (highest wins):

```
CLI flags  >  .yoto.toml (per-book sidecar)  >  ~/.config/ebook-to-yoto/config.toml  >  defaults
```

A default config is created at `~/.config/ebook-to-yoto/config.toml` on first run:

```toml
[tts]
engine = "chatterbox"         # kokoro | chatterbox | gemini | openai | elevenlabs
voice = ""                    # leave blank to use engine default
voice_ref = ""                # path to WAV for Chatterbox voice cloning (optional)
speed = 1.0

[icons]
engine = "stable-diffusion"   # stable-diffusion | gemini | openai
no_icons = false

[output]
split_cards = false
skip_existing = false
```

### Per-book sidecar

Create `my_book.yoto.toml` next to `my_book.epub` to set book-specific defaults:

```toml
[tts]
engine = "kokoro"
voice = "af_bella"
speed = 1.1
```

## Output structure

```
my_book_yoto/
├── 001-chapter-one.mp3
├── 001-chapter-one_icon.png
├── 002-chapter-two.mp3
├── 002-chapter-two_icon.png
├── ...
├── cover.jpg          # if present in source ebook
└── manifest.json      # pipeline metadata
```

### manifest.json

```json
{
  "book_title": "My Book",
  "tts_engine": "chatterbox",
  "tts_voice": "chatterbox-default",
  "icon_engine": "stable-diffusion",
  "generated_at": "2026-03-10T12:00:00",
  "tracks": [
    {"track": 1, "title": "Chapter One", "mp3": "001-chapter-one.mp3",
     "icon": "001-chapter-one_icon.png", "word_count": 1234, "icon_source": "generated"}
  ]
}
```

## Yoto limits

| Limit | Value |
|---|---|
| Max tracks per card | 100 |
| Max track duration | 60 minutes |
| Max track file size | 100 MB |
| Max total per card | 500 MB / 5 hours |

Use `--split-cards` for long books to auto-split into `card_1/`, `card_2/`, etc.

## Supported formats

| Format | Notes |
|---|---|
| EPUB | Full support including embedded images and cover |
| PDF | Text extraction via pypdf |
| TXT | Blank-line paragraph chunking |
| MOBI | Requires [Calibre](https://calibre-ebook.com/) (`brew install --cask calibre`) |

## Environment variables

| Variable | Used by |
|---|---|
| `HF_TOKEN` | FLUX.1-schnell icon generation |
| `OPENAI_API_KEY` | OpenAI TTS + DALL-E 3 icons |
| `GEMINI_API_KEY` | Gemini TTS + Imagen 3 icons |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS |

## Running tests

```bash
source .venv/bin/activate

# Fast tests only (no model loading)
pytest tests/ -m "not slow"

# All tests including slow TTS tests
pytest tests/
```

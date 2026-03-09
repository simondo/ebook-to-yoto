#!/usr/bin/env bash
# setup.sh — Install ebook-to-yoto dependencies on macOS Apple Silicon
# Idempotent: safe to run multiple times.
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[setup]${NC} $*"; }
warn()    { echo -e "${YELLOW}[setup]${NC} $*"; }
fail()    { echo -e "${RED}[setup] ERROR:${NC} $*" >&2; exit 1; }

# 1. Check Homebrew
info "Checking Homebrew..."
if ! command -v brew &>/dev/null; then
  fail "Homebrew is not installed. Install it from: https://brew.sh"
fi
info "Homebrew found: $(brew --version | head -1)"

# 2. Install ffmpeg
info "Installing ffmpeg..."
if brew list ffmpeg &>/dev/null; then
  info "ffmpeg already installed."
else
  brew install ffmpeg || fail "Failed to install ffmpeg"
fi

# 3. Install Calibre (for MOBI support)
info "Installing Calibre (for MOBI support)..."
if command -v ebook-convert &>/dev/null; then
  info "ebook-convert already on PATH."
else
  brew install --cask calibre || fail "Failed to install Calibre"
  # Calibre installs ebook-convert at a known path — add it if not on PATH
  CALIBRE_BIN="/Applications/calibre.app/Contents/MacOS"
  if [[ -d "$CALIBRE_BIN" ]] && ! echo "$PATH" | grep -q "$CALIBRE_BIN"; then
    warn "Calibre installed. You may need to restart your terminal or add to PATH:"
    warn "  export PATH=\"\$PATH:$CALIBRE_BIN\""
  fi
fi

# 4. Check / install Python 3.11
info "Checking Python 3.11..."
if command -v python3.11 &>/dev/null; then
  info "Python 3.11 found: $(python3.11 --version)"
else
  info "Installing python@3.11..."
  brew install python@3.11 || fail "Failed to install python@3.11"
fi

# 5. Create virtualenv
VENV_DIR="$HOME/.venvs/ebook-to-yoto"
info "Setting up virtualenv at $VENV_DIR..."
if [[ ! -d "$VENV_DIR" ]]; then
  python3.11 -m venv "$VENV_DIR" || fail "Failed to create virtualenv"
  info "Virtualenv created."
else
  info "Virtualenv already exists."
fi

# 6. Install package
info "Installing ebook-to-yoto..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -e "$SCRIPT_DIR[local]" \
  || fail "Failed to install ebook-to-yoto"

# 7. Add PYTORCH_ENABLE_MPS_FALLBACK to ~/.zshrc
ZSHRC="$HOME/.zshrc"
MPS_LINE='export PYTORCH_ENABLE_MPS_FALLBACK=1'
if grep -qF "$MPS_LINE" "$ZSHRC" 2>/dev/null; then
  info "PYTORCH_ENABLE_MPS_FALLBACK already set in ~/.zshrc"
else
  echo "" >> "$ZSHRC"
  echo "# Required for Chatterbox TTS on Apple Silicon" >> "$ZSHRC"
  echo "$MPS_LINE" >> "$ZSHRC"
  info "Added PYTORCH_ENABLE_MPS_FALLBACK=1 to ~/.zshrc"
fi

# 8. Done
echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Activate the environment and run:"
echo "  source $VENV_DIR/bin/activate"
echo "  ebook-to-yoto --help"
echo ""
echo "Or run without activating:"
echo "  $VENV_DIR/bin/ebook-to-yoto --help"
echo ""
echo "Note: Kokoro and Stable Diffusion models download automatically on first use."
echo "Note: Restart your terminal (or run 'source ~/.zshrc') to apply the MPS env var."

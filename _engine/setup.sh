#!/usr/bin/env bash
# ~/Documents/OCR_Sistema/_engine/setup.sh
set -euo pipefail

BASE="$HOME/Documents/OCR_Sistema"
ENGINE="$BASE/_engine"

echo "==> Installo dipendenze di sistema (Homebrew)..."
brew install ocrmypdf tesseract tesseract-lang ollama || true

echo "==> Avvio Ollama e scarico Qwen2.5 7B (~5GB)..."
ollama serve >/dev/null 2>&1 &
sleep 3
ollama pull qwen2.5:7b

echo "==> Creo virtualenv Python..."
cd "$ENGINE"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "==> Installo alias 'ocr-processa' e 'ocr-cerca'..."
SHELL_RC="$HOME/.zshrc"
grep -q "alias ocr-processa" "$SHELL_RC" 2>/dev/null || cat >> "$SHELL_RC" <<EOF

# OCR_Sistema
alias ocr-processa='"$ENGINE/.venv/bin/python" "$ENGINE/ocr_processa.py"'
alias ocr-cerca='"$ENGINE/.venv/bin/python" "$ENGINE/ocr_cerca.py"'
EOF

echo "==> Fatto. Apri un nuovo Terminale, poi usa: ocr-processa"

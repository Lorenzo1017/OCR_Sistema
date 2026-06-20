#!/usr/bin/env bash
# Setup OCR_Sistema per macOS e Linux.
# Uso: bash _engine/setup.sh   (dalla cartella OCR_Sistema, ovunque essa sia)
set -euo pipefail

ENGINE="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$ENGINE/.." && pwd)"
OS="$(uname -s)"
echo "==> OCR_Sistema in: $BASE   (OS: $OS)"

# --- 1. Dipendenze di sistema ---
if [ "$OS" = "Darwin" ]; then
  if ! command -v brew >/dev/null; then
    echo "Installa prima Homebrew: https://brew.sh"; exit 1
  fi
  echo "==> Installo tesseract, ocrmypdf, ollama (Homebrew)..."
  brew install ocrmypdf tesseract tesseract-lang ollama || true
elif [ "$OS" = "Linux" ]; then
  echo "==> Su Linux installa (una volta) con il tuo gestore pacchetti, es. Debian/Ubuntu:"
  echo "      sudo apt update && sudo apt install -y tesseract-ocr tesseract-ocr-ita ocrmypdf"
  echo "    e Ollama: curl -fsSL https://ollama.com/install.sh | sh"
  read -r -p "Premi Invio quando tesseract/ocrmypdf/ollama sono installati..."
fi

# --- 2. Virtualenv Python + dipendenze ---
echo "==> Creo virtualenv e installo dipendenze Python..."
python3 -m venv "$ENGINE/.venv"
"$ENGINE/.venv/bin/pip" -q install --upgrade pip
"$ENGINE/.venv/bin/pip" -q install -r "$ENGINE/requirements.txt"

# --- 3. Modello LLM ---
echo "==> Scarico il modello qwen2.5:7b (~5GB) se manca..."
ollama serve >/dev/null 2>&1 &
sleep 3
ollama pull qwen2.5:7b || true

# --- 4. Avvio automatico al login ---
PY="$ENGINE/.venv/bin/python"
if [ "$OS" = "Darwin" ]; then
  PLIST="$HOME/Library/LaunchAgents/com.ocrsistema.watch.plist"
  mkdir -p "$HOME/Library/LaunchAgents"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.ocrsistema.watch</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$ENGINE/watch.py</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$BASE/log_auto.txt</string>
  <key>StandardErrorPath</key><string>$BASE/log_auto.txt</string>
</dict></plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "==> Avvio automatico installato (LaunchAgent)."
elif [ "$OS" = "Linux" ]; then
  UNIT="$HOME/.config/systemd/user/ocrsistema.service"
  mkdir -p "$(dirname "$UNIT")"
  cat > "$UNIT" <<EOF
[Unit]
Description=OCR_Sistema watcher
[Service]
ExecStart=$PY $ENGINE/watch.py
Restart=always
[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now ocrsistema.service || \
    echo "(avvia a mano con: systemctl --user start ocrsistema.service)"
  echo "==> Avvio automatico installato (systemd user)."
fi

# --- 5. Alias comodi (zsh/bash) ---
RC="$HOME/.zshrc"; [ -n "${BASH_VERSION:-}" ] && RC="$HOME/.bashrc"
if ! grep -q "alias ocr-processa" "$RC" 2>/dev/null; then
  cat >> "$RC" <<EOF

# OCR_Sistema
alias ocr-processa='"$PY" "$ENGINE/ocr_processa.py"'
alias ocr-cerca='"$PY" "$ENGINE/ocr_cerca.py"'
EOF
fi

echo ""
echo "==> FATTO. Metti i documenti in: $BASE/inbox"
echo "    Vengono processati da soli e ordinati in: $BASE/archivio"

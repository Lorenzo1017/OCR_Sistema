#!/usr/bin/env bash
# ~/OCR_Sistema/_engine/setup.sh
set -euo pipefail

BASE="$HOME/OCR_Sistema"
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

echo "==> Installo alias 'ocr-processa', 'ocr-cerca', 'ocr-auto-on/off'..."
SHELL_RC="$HOME/.zshrc"
PLIST="$HOME/Library/LaunchAgents/com.ocrsistema.watch.plist"
grep -q "alias ocr-processa" "$SHELL_RC" 2>/dev/null || cat >> "$SHELL_RC" <<EOF

# OCR_Sistema
alias ocr-processa='"$ENGINE/.venv/bin/python" "$ENGINE/ocr_processa.py"'
alias ocr-cerca='"$ENGINE/.venv/bin/python" "$ENGINE/ocr_cerca.py"'
alias ocr-auto-on='launchctl load "$PLIST" && echo "Controllo automatico ATTIVO (ogni 5 min)"'
alias ocr-auto-off='launchctl unload "$PLIST" && echo "Controllo automatico SPENTO"'
EOF

echo "==> Installo controllo automatico (LaunchAgent, ogni 5 min)..."
chmod +x "$ENGINE/ocr_watch.sh"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.ocrsistema.watch</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$ENGINE/ocr_watch.sh</string>
  </array>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$BASE/log_auto_launchd.txt</string>
  <key>StandardErrorPath</key><string>$BASE/log_auto_launchd.txt</string>
</dict>
</plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo ""
echo "==> Fatto. Controllo automatico ATTIVO: ogni 5 minuti la cartella"
echo "    inbox/ viene controllata e i file processati da soli."
echo "    Tu guardi solo: archivio/ e _DaSmistare/"
echo ""
echo "    Comandi (in un nuovo Terminale):"
echo "      ocr-auto-off   spegne il controllo automatico"
echo "      ocr-auto-on    riaccende"
echo "      ocr-processa   forza subito un giro manuale"

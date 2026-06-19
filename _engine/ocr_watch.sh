#!/usr/bin/env bash
# Worker automatico: lanciato dal LaunchAgent ogni 5 minuti.
# Controlla inbox/, se ci sono file li processa. Altrimenti esce silenzioso.
# NB: la mutua esclusione (manuale vs automatico) e' gestita da ocr_processa.py
# tramite lock fcntl unico -> qui nessun lock proprio.
set -uo pipefail

BASE="$HOME/OCR_Sistema"
ENGINE="$BASE/_engine"
LOG="$BASE/log_auto.txt"

# Homebrew + binari di sistema nel PATH (launchd parte con PATH minimo)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Nessun file in inbox -> esci senza fare nulla (niente log spam)
shopt -s nullglob dotglob
files=("$BASE/inbox"/*)
[ ${#files[@]} -eq 0 ] && exit 0

# Assicura che Ollama sia attivo (serve per la classificazione).
# F4: poll fino a quando risponde davvero (max ~30s) invece di sleep fisso.
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  nohup ollama serve >/dev/null 2>&1 &
  for _ in $(seq 1 30); do
    curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') — ${#files[@]} file in inbox =====" >> "$LOG"
"$ENGINE/.venv/bin/python" "$ENGINE/ocr_processa.py" >> "$LOG" 2>&1
echo "" >> "$LOG"

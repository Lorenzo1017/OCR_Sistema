#!/usr/bin/env bash
# Worker automatico: lanciato dal LaunchAgent ogni 5 minuti.
# Controlla inbox/, se ci sono file li processa. Altrimenti esce silenzioso.
set -uo pipefail

BASE="$HOME/Documents/OCR_Sistema"
ENGINE="$BASE/_engine"
LOG="$BASE/log_auto.txt"
LOCKDIR="$BASE/.watch.lock"

# Homebrew + binari di sistema nel PATH (launchd parte con PATH minimo)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Lock atomico (mkdir): evita run sovrapposti se un batch dura >5 min.
# Pulisci lock vecchio (>2h) lasciato da un processo morto.
if [ -d "$LOCKDIR" ]; then
  if [ -n "$(find "$LOCKDIR" -maxdepth 0 -mmin +120 2>/dev/null)" ]; then
    rmdir "$LOCKDIR" 2>/dev/null || true
  fi
fi
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  exit 0   # un altro run è già in corso
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

# Nessun file in inbox -> esci senza fare nulla (niente log spam)
shopt -s nullglob dotglob
files=("$BASE/inbox"/*)
[ ${#files[@]} -eq 0 ] && exit 0

# Assicura che Ollama sia attivo (serve per la classificazione)
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  nohup ollama serve >/dev/null 2>&1 &
  sleep 5
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') — ${#files[@]} file in inbox =====" >> "$LOG"
"$ENGINE/.venv/bin/python" "$ENGINE/ocr_processa.py" >> "$LOG" 2>&1
echo "" >> "$LOG"

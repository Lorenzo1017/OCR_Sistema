#!/usr/bin/env bash
# Worker automatico: lanciato dal LaunchAgent ogni 5 minuti.
# Controlla inbox/, se ci sono file li processa. Altrimenti esce silenzioso.
# NB: la mutua esclusione (manuale vs automatico) e' gestita da ocr_processa.py
# tramite lock fcntl unico -> qui nessun lock proprio.
set -uo pipefail

BASE="$HOME/OCR_Sistema"
ENGINE="$BASE/_engine"
LOG="$BASE/log_auto.txt"
MODEL="qwen2.5:7b"
API="http://localhost:11434/api/tags"

# Homebrew + binari di sistema nel PATH (launchd parte con PATH minimo)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Nessun file in inbox -> esci senza fare nulla (niente log spam, Ollama resta a riposo)
shopt -s nullglob dotglob
files=("$BASE/inbox"/*)
[ ${#files[@]} -eq 0 ] && exit 0

# --- Ollama: avvialo SOLO se non gia' attivo (cosi' non disturba altri progetti) ---
STARTED_OLLAMA=0
OLLAMA_PID=""
if ! curl -s "$API" >/dev/null 2>&1; then
  nohup ollama serve >/dev/null 2>&1 &
  OLLAMA_PID=$!
  STARTED_OLLAMA=1
  # poll readiness (max ~30s) invece di sleep fisso
  for _ in $(seq 1 30); do
    curl -s "$API" >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') — ${#files[@]} file in inbox =====" >> "$LOG"
"$ENGINE/.venv/bin/python" "$ENGINE/ocr_processa.py" >> "$LOG" 2>&1
echo "" >> "$LOG"

# --- Riporta Ollama a riposo ---
# scarica il modello dalla RAM (~5GB liberati). keep_alive breve fa comunque
# scaricare da solo poco dopo, questo lo rende immediato.
ollama stop "$MODEL" >/dev/null 2>&1 || true
# se siamo stati NOI ad avviare il server, fermalo -> Ollama torna a 0.
# se era gia' acceso (altro progetto/Ollama.app), lo lasciamo stare.
if [ "$STARTED_OLLAMA" = "1" ] && [ -n "$OLLAMA_PID" ]; then
  kill "$OLLAMA_PID" >/dev/null 2>&1 || true
fi

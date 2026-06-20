# 📂 OCR_Sistema

![tests](https://github.com/Lorenzo1017/OCR_Sistema/actions/workflows/test.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![OS](https://img.shields.io/badge/OS-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

Catalogazione automatica di documenti scansionati, **100% locale e offline**.
Butti le scansioni in una cartella; il sistema fa OCR, capisce di cosa si tratta
con un modello LLM locale, **rinomina** ogni file con data e contenuto e lo
**smista** in un albero di cartelle tematiche. Nessun dato lascia il computer.

```
inbox/bolletta_scansionata.pdf
   └─► archivio/Casa/Utenze/Gas/2024-03-15_Enel_bolletta_gas.pdf
```

## Caratteristiche
- **Offline e privato**: OCR (Tesseract) + LLM locale (Ollama + Qwen2.5) — zero cloud.
- **Automatico**: un watcher controlla la `inbox/` ogni 15 minuti e processa da solo.
- **Rinomina parlante**: `AAAA-MM-GG_Mittente_Tipo_Dettaglio.pdf`.
- **Smistamento tematico**: albero di categorie configurabile (`categorie.yaml`).
- **Sicuro**: originali sempre salvati; documenti incerti in `_DaSmistare/` (mai
  catalogati a caso); operazioni reversibili; ricerca full-text (SQLite FTS5).
- **Cross-platform**: macOS, Linux, Windows. Notifiche native.
- **Ollama a riposo**: il modello (~5GB) viene scaricato dalla RAM a fine lavoro.

## Requisiti
- Python 3.9+
- [Tesseract](https://github.com/tesseract-ocr/tesseract) (lingua *ita*),
  [OCRmyPDF](https://ocrmypdf.readthedocs.io/), [Ollama](https://ollama.com) +
  modello `qwen2.5:7b`
- RAM: minimo 8GB, consigliati 16GB · Disco: ≥10GB liberi

## Installazione
```bash
# macOS / Linux
bash _engine/setup.sh
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File _engine\setup.ps1
```
Il setup verifica l'**hardware**, installa le componenti (incluso il modello LLM)
e configura l'avvio automatico (LaunchAgent / systemd / Task Scheduler).

## Uso
1. Metti i documenti (PDF o immagini) in `inbox/`.
2. Entro 15 minuti vengono processati e ordinati in `archivio/`.
3. Controlla `_DaSmistare/` per i pochi documenti incerti.

Comandi: `ocr-check` (diagnostica hardware/componenti), `ocr-processa` (forza un
giro), `ocr-cerca "parole"` (ricerca full-text).

Dettagli e portabilità: vedi [README_PORTABILITA.md](README_PORTABILITA.md),
[GUIDA.md](GUIDA.md), [CHECKLIST.md](CHECKLIST.md).

## Test
```bash
cd _engine && .venv/bin/python -m pytest tests/ -q
```

## Architettura
- `_engine/ocrsys/` — moduli (config, ocr, classify, pipeline, runner, db,
  taxonomy, dates, naming, locking, notify, ollama_mgr, hardware, preflight)
- `_engine/watch.py` — daemon cross-OS · `_engine/ocr_processa.py` / `ocr_cerca.py`
  / `check.py` — comandi
- dati (gitignored): `inbox/ archivio/ originali/ text/ _DaSmistare/`

## Licenza
[MIT](LICENSE) © 2026 Lorenzo Chieregato

# Project summary — OCR_Sistema

**Version 1.0** · June 2026 · Lorenzo Chieregato · MIT license

A system for the automatic filing of scanned documents, **100% local and offline**.
Put your scans in a folder; the system runs OCR, classifies them with a local LLM,
renames them, and sorts them into topic folders on its own.

---

## What it does

- **OCR** offline (Tesseract + OCRmyPDF, Italian language) with automatic deskew
  and rotation of crooked scans.
- **Classification** with a local LLM (Ollama + Qwen2.5 7B): it extracts date,
  sender, type, detail and category by reading the text.
- **Meaningful renaming**: `YYYY-MM-DD_Sender_Type_Detail.pdf`.
- **Sorting** into a configurable category tree (`categorie.yaml`); uncertain
  documents go to `_DaSmistare/` (never filed at random).
- **Full-text search** across the whole archive (SQLite FTS5).
- **Automatic**: a watcher checks `inbox/` every 15 minutes.
- **Native notifications** (macOS/Linux/Windows) at start and end of processing.
- **Ollama at rest**: the model (~5GB) is unloaded from RAM after use.

## Safety and robustness

- Originals are always saved in `originali/` (backup keyed by content).
- Reversible operations (rename log); the system never deletes the archive.
- Files that fail repeatedly → quarantine (`_DaSmistare/_errori/`).
- Single lock shared between manual and automatic runs (no conflicts).
- Anti-misclassification guard for utilities (water/electricity/gas/internet/phone).
- Hardware (`ocr-check`) and dependency checks before use.

## Portability

Cross-platform app (macOS, Linux, Windows). The folder can be moved/copied
anywhere; on a new computer just run your OS's setup (`setup.sh` or `setup.ps1`),
which installs every component including the LLM model and configures automatic
startup (LaunchAgent / systemd / Task Scheduler).

## Quality

- **54 automated tests** (unit + integration with fakes).
- Validated end-to-end on real and synthetic documents.
- Two adversarial code reviews: all real correctness, robustness and cross-OS
  security bugs were fixed.
- CI on GitHub Actions: tests run on every push.

## Main commands

| Command | Action |
|---|---|
| `ocr-check` | hardware + component diagnostics |
| `ocr-processa` | run a processing pass now |
| `ocr-cerca "words"` | full-text search in the archive |

## Structure

```
OCR_Sistema/
├── inbox/  archivio/  originali/  text/  _DaSmistare/   (data, not versioned)
├── categorie.yaml                                       (category tree)
├── _engine/
│   ├── ocrsys/        modules: config, ocr, classify, pipeline, runner, db,
│   │                  taxonomy, dates, naming, locking, notify, ollama_mgr,
│   │                  hardware, preflight
│   ├── watch.py       cross-OS daemon
│   ├── ocr_processa.py · ocr_cerca.py · check.py   commands
│   ├── setup.sh · setup.ps1                          per-OS installers
│   └── tests/         54 tests
└── README.md · README_PORTABILITA.md · GUIDA.md · CHECKLIST.md · LICENSE
```

---

*Repository: https://github.com/Lorenzo1017/OCR_Sistema*

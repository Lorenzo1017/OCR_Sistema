# 🌍 OCR_Sistema — Portable app (macOS · Linux · Windows)

This folder **is the application**. You can move it, copy it, or paste it wherever
you like (another folder, a USB drive, another computer). The code has no hardcoded
paths: it adapts to wherever the folder is located.

## What is portable and what is not

| Item | Portable by copy-paste? |
|---|---|
| Code (`_engine/`), `categorie.yaml`, documents (`inbox/`, `archivio/`…) | ✅ Yes, anywhere and on any OS |
| Python environment (`_engine/.venv/`) | ❌ OS-specific → it is **recreated** by the setup |
| External programs (Tesseract, OCRmyPDF, Ollama) | ❌ They are **installed** once per OS |

In short: **copy the folder** → on a new computer **run the setup** for its
operating system (it recreates the environment and installs the automatic startup). Done.

## Installation by operating system

### 🍎 macOS / 🐧 Linux
```bash
cd /path/to/folder/OCR_Sistema
bash _engine/setup.sh
```
It installs the programs (on macOS via Homebrew), creates the Python environment,
downloads the model, and configures automatic startup (LaunchAgent on macOS,
systemd on Linux).

### 🪟 Windows
1. Install once: **Tesseract** (with the *ita* language), **Ghostscript**,
   **OCRmyPDF**, **Ollama** (links shown by the script).
2. In PowerShell, inside the folder:
   ```powershell
   powershell -ExecutionPolicy Bypass -File _engine\setup.ps1
   ```
   It creates the environment, downloads the model, and registers automatic startup (Task Scheduler).

## How it works (the same on every OS)

- A **watcher** (`watch.py`) checks `inbox/` every 15 minutes.
- If it finds documents: it starts Ollama, runs OCR, classifies, renames, sorts into
  `archivio/`, then **unloads the model and stops Ollama** (back to idle).
- You receive a **notification** at startup and when the job finishes (each OS's native notification).
- Uncertain documents end up in `_DaSmistare/`; the originals are saved in
  `originali/`.

## Manual commands (optional)

| Action | macOS/Linux | Windows |
|---|---|---|
| Process now | `ocr-processa` | `_engine\.venv\Scripts\python _engine\ocr_processa.py` |
| Search for a document | `ocr-cerca "words"` | `…\python _engine\ocr_cerca.py "words"` |
| Start the watcher manually | `_engine/.venv/bin/python _engine/watch.py` | `…\python _engine\watch.py` |

## Moving the folder (same computer)
Go ahead and move it. Then re-run the setup for your OS **only** to update the
automatic startup to the new paths (it does not re-download anything if already present).
Alternatively, you can force the location of the data with the environment variable
`OCR_SISTEMA_HOME`.

## Check / diagnostics
To inspect **hardware and components** at any time:
```bash
# macOS/Linux
ocr-check            # or:  _engine/.venv/bin/python _engine/check.py
# Windows
_engine\.venv\Scripts\python _engine\check.py
```
It shows RAM/CPU/disk, tells you whether the hardware is adequate, and — if a component
is missing — prints the **exact command** to install it (Tesseract, OCRmyPDF, Ollama, model).
The `setup` runs this check automatically before downloading the model.

## Hardware requirements
- **Python 3.9+**
- **Tesseract** (with the *ita* language data), **OCRmyPDF**, **Ollama** + the
  `qwen2.5:7b` model (~5GB).
- **RAM**: minimum 8GB, **16GB recommended** (the model uses ~5GB only during
  processing).
- **Disk**: at least 10GB free (model + documents).
- **CPU**: 4+ cores recommended.

## Common problems
- *"Environment not ready: missing …"* → a program is missing: install it (see above).
- *No notifications* → the first time, allow notifications in the OS settings
  (on Linux you need `notify-send`).
- *It doesn't start on its own* → restart the computer or re-run the setup.
- Tests: `cd _engine && .venv/bin/python -m pytest tests/ -q`.

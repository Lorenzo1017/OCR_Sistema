import os
from pathlib import Path

# BASE = cartella dell'applicazione (questo file e' in _engine/ocrsys/config.py,
# quindi parents[2] = la radice OCR_Sistema). Relativo al codice -> la cartella
# si puo' SPOSTARE/COPIARE ovunque (anche su Windows/Linux) senza modifiche.
# Override opzionale con la variabile d'ambiente OCR_SISTEMA_HOME.
BASE = Path(os.environ.get("OCR_SISTEMA_HOME",
                           Path(__file__).resolve().parents[2]))

# Aggiunge le dir bin comuni al PATH: gli scheduler (launchd/systemd/Task
# Scheduler) partono con PATH minimo e non troverebbero tesseract/ollama.
if os.name == "nt":
    _localapp = os.environ.get("LOCALAPPDATA", "")
    _extra = [
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files\Ghostscript\bin",
        os.path.join(_localapp, "Programs", "Ollama") if _localapp else "",
        os.path.join(_localapp, "Programs", "Tesseract-OCR") if _localapp else "",
    ]
else:
    _extra = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"]

_cur = os.environ.get("PATH", "")
for _p in _extra:
    if _p and _p not in _cur.split(os.pathsep):
        _cur = _cur + os.pathsep + _p
os.environ["PATH"] = _cur

INBOX = BASE / "inbox"
ARCHIVIO = BASE / "archivio"
ORIGINALI = BASE / "originali"
TEXT = BASE / "text"
DA_SMISTARE = BASE / "_DaSmistare"

DA_SMISTARE_ERRORI = DA_SMISTARE / "_errori"   # quarantena file irrecuperabili

CATEGORIE_YAML = BASE / "categorie.yaml"
DB_PATH = BASE / "index.db"
LOG_RINOMINE = BASE / "log_rinomine.csv"
LOG_ERRORI = BASE / "log_errori.csv"
LOCK_PATH = BASE / ".ocr.lock"                 # lock unico manuale+automatico

MAX_TENTATIVI = 3   # dopo N fallimenti su uno stesso file -> quarantena

OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
WATCH_INTERVAL = 900   # secondi tra un controllo inbox e il successivo (15 min)
# keep_alive breve: il modello (~5GB) si scarica da solo poco dopo l'ultimo
# uso OCR -> Ollama torna a riposo, RAM liberata.
OLLAMA_KEEP_ALIVE = "30s"

# Sotto questa lunghezza di testo OCR si ritenta con --force-ocr (F5).
OCR_MIN_TEXT = 20

INPUT_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

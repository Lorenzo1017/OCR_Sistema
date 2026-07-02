import os
from pathlib import Path

import yaml

# SISTEMA = cartella che contiene il codice e i file di sistema (questo file e'
# in <SISTEMA>/_engine/ocrsys/config.py -> parents[2] = SISTEMA).
SISTEMA = Path(__file__).resolve().parents[2]
# ROOT = dove vivono le cartelle utente (inbox/archivio/_DaSmistare). Se il
# codice e' dentro una cartella chiamata "_Sistema" (layout riordinato), ROOT e'
# il livello sopra; altrimenti (clone flat) ROOT == SISTEMA. Override con env.
_root = SISTEMA.parent if SISTEMA.name == "_Sistema" else SISTEMA
ROOT = Path(os.environ.get("OCR_SISTEMA_HOME", _root))
BASE = ROOT   # compatibilita': percorsi archivio relativi a ROOT

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

# cartelle utente (in primo piano, sotto ROOT)
INBOX = ROOT / "inbox"
ARCHIVIO = ROOT / "archivio"
DA_SMISTARE = ROOT / "_DaSmistare"
DA_SMISTARE_ERRORI = DA_SMISTARE / "_errori"   # quarantena file irrecuperabili

# file/cartelle di sistema (dentro _Sistema quando riordinato)
ORIGINALI = SISTEMA / "originali"
TEXT = SISTEMA / "text"
CATEGORIE_YAML = SISTEMA / "categorie.yaml"
DB_PATH = SISTEMA / "index.db"
LOG_RINOMINE = SISTEMA / "log_rinomine.csv"
LOG_ERRORI = SISTEMA / "log_errori.csv"
LOCK_PATH = SISTEMA / ".ocr.lock"              # lock unico manuale+automatico
EMAIL_CONFIG = SISTEMA / ".email.yaml"         # credenziali IMAP (gitignorato)
EMAIL_STATE = SISTEMA / ".email_stato.json"    # data attivazione + Message-ID visti
EMAIL_LOCK = SISTEMA / ".email.lock"           # evita fetch email concorrenti

MAX_TENTATIVI = 3   # dopo N fallimenti su uno stesso file -> quarantena

OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_VISION_MODEL = "qwen2.5vl:7b"   # fallback OCR vision (legge l'immagine)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
WATCH_INTERVAL = 900   # secondi tra un controllo inbox e il successivo (15 min)
# keep_alive breve: il modello (~5GB) si scarica da solo poco dopo l'ultimo
# uso OCR -> Ollama torna a riposo, RAM liberata.
OLLAMA_KEEP_ALIVE = "5m"

# Sotto questa lunghezza di testo OCR si ritenta con --force-ocr (F5).
OCR_MIN_TEXT = 20

# Se il PDF ha gia' almeno questo testo estraibile (firmati digitalmente, PEC,
# export nativi), si usa direttamente SENZA OCR: ocrmypdf rifiuterebbe i firmati
# (DigitalSignatureError) e per i nativi l'OCR e' inutile e piu' lento.
TESTO_NATIVO_MIN = 100

INPUT_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}


def ensure_dirs():
    """Crea le cartelle dati se mancano (es. dopo un clone fresco da GitHub,
    dove sono gitignorate). Idempotente."""
    for d in (INBOX, ARCHIVIO, ORIGINALI, TEXT, DA_SMISTARE):
        d.mkdir(parents=True, exist_ok=True)

# Impostazioni opzionali editabili dall'utente (impostazioni.yaml).
IMPOSTAZIONI_YAML = SISTEMA / "impostazioni.yaml"


def leggi_impostazioni(path) -> dict:
    """Legge impostazioni.yaml se presente; dict vuoto se manca/è invalido."""
    try:
        p = Path(path)
        if p.exists():
            data = yaml.safe_load(p.read_text())
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


_IMP = leggi_impostazioni(IMPOSTAZIONI_YAML)

# Lingue OCR per Tesseract (es. "ita", "ita+eng"). Richiede i language pack
# installati. Override in impostazioni.yaml -> ocr_lingue.
OCR_LINGUE = str(_IMP.get("ocr_lingue", "ita"))

# Quanti documenti OCR-are in parallelo (l'OCR e' CPU-bound; la classificazione
# LLM resta seriale). Default = core-2, max 4 (per non saturare RAM/Tesseract).
# Override in impostazioni.yaml -> ocr_workers.
OCR_WORKERS = int(_IMP.get("ocr_workers", max(1, min(4, (os.cpu_count() or 4) - 2))))

# Se True, salva una copia degli originali in _Sistema/originali/originali.zip.
# Override in impostazioni.yaml -> backup_originali: false (l'archivio e' gia'
# la copia catalogata; disattivandolo non si tiene l'originale pristino).
BACKUP_ORIGINALI = bool(_IMP.get("backup_originali", True))

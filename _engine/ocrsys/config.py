from pathlib import Path

BASE = Path.home() / "OCR_Sistema"

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

INPUT_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

"""Backup giornaliero dell'indice (DB) + configurazione. L'archivio dei PDF vive
gia' sul disco; la parte fragile e' il DB (metadati, ricerca): se si corrompe si
perde la catalogazione. Qui se ne fa uno snapshot CONSISTENTE (API di backup
SQLite, sicura anche in WAL mentre il daemon scrive) con rotazione.

Uso: ocr-backup-db [--tieni N]   (default: tiene gli ultimi 7)
Automatico: LaunchAgent com.ocrsistema.backup (giornaliero).
"""
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config


def _dir() -> Path:
    d = config.ROOT / "esportazioni" / "backup_db"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _snapshot(dest: Path):
    """Copia consistente del DB anche se un altro processo sta scrivendo."""
    src = sqlite3.connect(str(config.DB_PATH), timeout=30)
    try:
        out = sqlite3.connect(str(dest))
        try:
            src.backup(out)      # backup online atomico
        finally:
            out.close()
    finally:
        src.close()


def esegui(tieni: int = 7, oggi: str = None) -> Path:
    d = _dir()
    giorno = oggi or date.today().isoformat()
    dest = d / f"index_{giorno}.db"
    _snapshot(dest)
    # allega la configurazione (piccola) accanto al db del giorno
    for extra in (config.CATEGORIE_YAML, config.IMPOSTAZIONI_YAML):
        if extra.exists():
            shutil.copy2(extra, d / f"{giorno}_{extra.name}")
    # rotazione: tieni solo gli ultimi N snapshot del DB (+ relativi yaml)
    snapshot = sorted(d.glob("index_*.db"))
    for vecchio in snapshot[:-tieni] if tieni > 0 else []:
        giorno_v = vecchio.stem.replace("index_", "")
        vecchio.unlink(missing_ok=True)
        for y in d.glob(f"{giorno_v}_*"):
            y.unlink(missing_ok=True)
    return dest


def main():
    tieni = 7
    if "--tieni" in sys.argv:
        tieni = int(sys.argv[sys.argv.index("--tieni") + 1])
    dest = esegui(tieni)
    n = len(list(_dir().glob("index_*.db")))
    print(f"Backup DB: {dest}  (snapshot conservati: {n})")


if __name__ == "__main__":
    main()

"""Esportazioni: indice CSV, zip per categoria, zip da ricerca, backup completo.
Usato dal comando ocr-esporta e dalla web UI. Output in <ROOT>/esportazioni/."""
import csv
import zipfile
from datetime import datetime
from pathlib import Path

from . import config

_CAMPI = ["data_documento", "mittente", "tipo", "categoria", "tags",
          "nome_file", "percorso", "confidenza", "n_pagine"]


def _out_dir() -> Path:
    d = config.ROOT / "esportazioni"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def indice_csv(db, dest: Path = None) -> Path:
    """Esporta l'intero catalogo in CSV (delimitatore ';' -> Excel italiano)."""
    dest = dest or _out_dir() / f"indice_{_stamp()}.csv"
    rows = db.conn.execute(
        f"SELECT {', '.join(_CAMPI)} FROM documenti "
        "ORDER BY categoria, data_documento").fetchall()
    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(_CAMPI)
        for r in rows:
            w.writerow(list(r))
    return dest


def _zip_files(percorsi, dest: Path) -> tuple:
    """Zippa i percorsi (relativi a BASE) in dest. Ritorna (aggiunti, mancanti)."""
    aggiunti = mancanti = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in percorsi:
            src = config.BASE / rel
            if src.exists():
                z.write(src, rel)
                aggiunti += 1
            else:
                mancanti += 1
    return aggiunti, mancanti


def zip_categoria(db, categoria: str, dest: Path = None) -> tuple:
    """Zip dei PDF di una categoria (incluse sottocartelle anno).
    Ritorna (path_zip, aggiunti, mancanti); path_zip None se categoria vuota."""
    categoria = categoria.strip("/")
    rows = db.conn.execute(
        "SELECT percorso FROM documenti WHERE categoria = ? ORDER BY percorso",
        (categoria,)).fetchall()
    if not rows:
        return None, 0, 0
    safe = categoria.replace("/", "_")
    dest = dest or _out_dir() / f"categoria_{safe}_{_stamp()}.zip"
    agg, man = _zip_files([r[0] for r in rows], dest)
    return dest, agg, man


def zip_ricerca(db, query: str, dest: Path = None) -> tuple:
    """Zip dei PDF che corrispondono alla ricerca FTS.
    Ritorna (path_zip, aggiunti, mancanti); path_zip None se nessun risultato."""
    risultati = db.search(query)
    if not risultati:
        return None, 0, 0
    safe = "".join(c if c.isalnum() else "_" for c in query)[:40]
    dest = dest or _out_dir() / f"ricerca_{safe}_{_stamp()}.zip"
    agg, man = _zip_files([r["percorso"] for r in risultati], dest)
    return dest, agg, man


def backup_completo(dest: Path = None) -> Path:
    """Zip unico: archivio + indice DB + configurazione. Per backup/migrazione."""
    dest = dest or _out_dir() / f"backup_{_stamp()}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(config.ARCHIVIO.rglob("*")):
            if p.is_file() and p.name != ".DS_Store":
                z.write(p, p.relative_to(config.BASE))
        for extra in (config.DB_PATH, config.CATEGORIE_YAML,
                      config.IMPOSTAZIONI_YAML):
            if extra.exists():
                z.write(extra, Path("_Sistema") / extra.name)
    return dest

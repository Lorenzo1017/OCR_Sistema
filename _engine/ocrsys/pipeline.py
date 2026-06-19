import csv
import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import config
from .db import Database
from .dates import extract_date, normalize_date
from .naming import build_name, resolve_collision
from .taxonomy import Taxonomy


@dataclass
class Context:
    base: Path
    taxonomy: Taxonomy
    db: Database
    ocr_to_pdf: Callable
    extract_text: Callable
    classify: Callable


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _log_rinomina(base: Path, originale: str, nuovo: str):
    log = base / "log_rinomine.csv"
    new = not log.exists()
    with log.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["originale", "nuovo"])
        w.writerow([originale, nuovo])


def process_file(src: Path, ctx: Context) -> str:
    """Processa un singolo file. Ritorna 'ok' | 'skip' | 'dasmistare'."""
    sha = _sha256(src)
    if ctx.db.already_processed(sha):
        return "skip"

    backup = ctx.base / "originali" / src.name
    if not backup.exists():
        shutil.copy2(src, backup)

    with tempfile.TemporaryDirectory() as td:
        tmp_pdf = Path(td) / "ocr.pdf"
        ctx.ocr_to_pdf(src, tmp_pdf)
        text, n_pagine = ctx.extract_text(tmp_pdf)

        (ctx.base / "text" / f"{src.stem}.txt").write_text(text)

        meta = ctx.classify(text, ctx.taxonomy)
        # Qwen puo' restituire data in formati vari (15/03/2024): normalizza
        # sempre in AAAA-MM-GG, con fallback all'estrazione dal testo.
        data = normalize_date(meta.get("data")) or extract_date(text)

        if meta.get("valido") and ctx.taxonomy.is_valid(meta["categoria"]):
            dest_dir = ctx.base / "archivio" / meta["categoria"]
            name = build_name(data, meta["mittente"], meta["tipo"],
                              meta["dettaglio"])
            status = "ok"
        else:
            dest_dir = ctx.base / "_DaSmistare"
            name = build_name(None, meta.get("mittente", ""),
                              meta.get("tipo", "documento"),
                              meta.get("dettaglio", ""))
            status = "dasmistare"

        dest_dir.mkdir(parents=True, exist_ok=True)
        name = resolve_collision(dest_dir, name)
        shutil.move(str(tmp_pdf), str(dest_dir / name))

    rel = (dest_dir / name).relative_to(ctx.base)
    ctx.db.insert({
        "nome_file": name, "percorso": str(rel),
        "categoria": meta.get("categoria", "_DaSmistare"),
        "data_documento": data or "0000-00-00",
        "mittente": meta.get("mittente", ""), "tipo": meta.get("tipo", ""),
        "testo_completo": text, "n_pagine": n_pagine,
        "confidenza": meta.get("confidenza", "bassa"), "sha256": sha,
    })
    _log_rinomina(ctx.base, src.name, str(rel))
    return status


def build_default_context() -> Context:
    from .ocr import ocr_to_pdf, extract_text
    from .classify import classify
    return Context(
        base=config.BASE,
        taxonomy=Taxonomy.load(config.CATEGORIE_YAML),
        db=Database(config.DB_PATH),
        ocr_to_pdf=ocr_to_pdf, extract_text=extract_text, classify=classify,
    )

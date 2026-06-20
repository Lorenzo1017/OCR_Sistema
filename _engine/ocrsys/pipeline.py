import csv
import hashlib
import shutil
import tempfile
import zipfile
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
    base: Path            # ROOT, per relative_to dei percorsi archiviati
    archivio: Path
    da_smistare: Path
    originali: Path
    text: Path
    log_rinomine: Path
    taxonomy: Taxonomy
    db: Database
    ocr_to_pdf: Callable
    extract_text: Callable
    classify: Callable
    backup_originali: bool = True


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _backup_zip(originali_dir: Path, src: Path, sha: str):
    """Salva l'originale dentro originali/originali.zip (nome interno con
    prefisso sha). Salta se gia' presente."""
    zip_path = originali_dir / "originali.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    arcname = f"{sha[:10]}_{src.name}"
    with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as z:
        if arcname not in z.namelist():
            z.write(src, arcname)


def _log_rinomina(log: Path, originale: str, nuovo: str):
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["originale", "nuovo"])
        w.writerow([originale, nuovo])


def _classifica(src, ctx, text, conferma):
    """Classificazione LLM + data normalizzata (+ eventuale conferma)."""
    try:
        mittenti = ctx.db.known_senders()
    except Exception:
        mittenti = None
    meta = ctx.classify(text, ctx.taxonomy, mittenti)
    # Qwen puo' restituire data in formati vari (15/03/2024): normalizza sempre
    # in AAAA-MM-GG, con fallback all'estrazione dal testo.
    data = normalize_date(meta.get("data")) or extract_date(text)
    if conferma is not None:
        meta, data = conferma(src.name, meta, data)
    return meta, data


def _classify_doc(src, ctx, tmp_pdf, conferma):
    """(per dry-run) estrae testo + classifica. Ritorna (text, n, meta, data)."""
    text, n_pagine = ctx.extract_text(tmp_pdf)
    meta, data = _classifica(src, ctx, text, conferma)
    return text, n_pagine, meta, data


def _ocr_to_job(src: Path, sha: str, ctx) -> dict:
    """Fase OCR (parallelizzabile): produce un PDF temporaneo persistente +
    testo. Il tempdir va ripulito dopo il commit. NIENTE accesso al DB/Ollama
    qui (cosi' e' sicuro lanciarlo su piu' thread)."""
    tmpdir = Path(tempfile.mkdtemp(prefix="ocrsys_"))
    tmp_pdf = tmpdir / "ocr.pdf"
    ctx.ocr_to_pdf(src, tmp_pdf)
    text, n_pagine = ctx.extract_text(tmp_pdf)
    return {"src": src, "sha": sha, "tmpdir": tmpdir,
            "tmp_pdf": tmp_pdf, "text": text, "n": n_pagine}


def _commit_job(job: dict, ctx, conferma=None) -> str:
    """Fase commit (SERIALE): classifica (Ollama), archivia, indicizza."""
    src, sha, tmp_pdf = job["src"], job["sha"], job["tmp_pdf"]
    text, n_pagine = job["text"], job["n"]
    try:
        if ctx.backup_originali:
            _backup_zip(ctx.originali, src, sha)
        meta, data = _classifica(src, ctx, text, conferma)
        ctx.text.mkdir(parents=True, exist_ok=True)
        (ctx.text / f"{sha[:10]}_{src.stem}.txt").write_text(
            text, encoding="utf-8", errors="replace")
        dest_dir, name, status = _destinazione(ctx, meta, data)
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = resolve_collision(dest_dir, name)
        shutil.move(str(tmp_pdf), str(dest_dir / name))
        rel = (dest_dir / name).relative_to(ctx.base)
        ctx.db.insert({
            "nome_file": name, "percorso": str(rel),
            "categoria": meta.get("categoria", "_DaSmistare"),
            "data_documento": data or "0000-00-00",
            "mittente": meta.get("mittente", ""), "tipo": meta.get("tipo", ""),
            "tags": " ".join(meta.get("tags") or []),
            "testo_completo": text, "n_pagine": n_pagine,
            "confidenza": meta.get("confidenza", "bassa"), "sha256": sha,
        })
        _log_rinomina(ctx.log_rinomine, src.name, str(rel))
        return status
    finally:
        shutil.rmtree(job["tmpdir"], ignore_errors=True)


def _destinazione(ctx, meta, data):
    """Ritorna (dest_dir, name, status) in base alla validità della classifica."""
    if meta.get("valido") and ctx.taxonomy.is_valid(meta["categoria"]):
        dest_dir = ctx.archivio / meta["categoria"]
        name = build_name(data, meta["mittente"], meta["tipo"], meta["dettaglio"])
        status = "ok"
    else:
        dest_dir = ctx.da_smistare
        name = build_name(None, meta.get("mittente", ""),
                          meta.get("tipo", "documento"), meta.get("dettaglio", ""))
        status = "dasmistare"
    return dest_dir, name, status


def plan_file(src: Path, ctx: Context, conferma=None) -> dict:
    """DRY-RUN: calcola dove finirebbe il file SENZA toccare nulla (no backup,
    no move, no db, no log). Ritorna {'status', 'dest'} (dest relativo a base)."""
    sha = _sha256(src)
    if ctx.db.already_processed(sha):
        return {"status": "skip", "dest": None}
    with tempfile.TemporaryDirectory() as td:
        tmp_pdf = Path(td) / "ocr.pdf"
        ctx.ocr_to_pdf(src, tmp_pdf)
        _, _, meta, data = _classify_doc(src, ctx, tmp_pdf, conferma)
        dest_dir, name, status = _destinazione(ctx, meta, data)
        name = resolve_collision(dest_dir, name)
        return {"status": status, "dest": str((dest_dir / name).relative_to(ctx.base))}


def process_file(src: Path, ctx: Context, conferma=None) -> str:
    """Processa un singolo file (OCR + commit). Ritorna 'ok'|'skip'|'dasmistare'.
    `conferma(nome, meta, data) -> (meta, data)` permette correzione interattiva."""
    sha = _sha256(src)
    if ctx.db.already_processed(sha):
        return "skip"
    job = _ocr_to_job(src, sha, ctx)
    return _commit_job(job, ctx, conferma)


def build_default_context() -> Context:
    from .ocr import ocr_to_pdf, extract_text
    from .classify import classify
    return Context(
        base=config.BASE,
        archivio=config.ARCHIVIO, da_smistare=config.DA_SMISTARE,
        originali=config.ORIGINALI, text=config.TEXT,
        log_rinomine=config.LOG_RINOMINE,
        taxonomy=Taxonomy.load(config.CATEGORIE_YAML),
        db=Database(config.DB_PATH),
        ocr_to_pdf=ocr_to_pdf, extract_text=extract_text, classify=classify,
        backup_originali=config.BACKUP_ORIGINALI,
    )

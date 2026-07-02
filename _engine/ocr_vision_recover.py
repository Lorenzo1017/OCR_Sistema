"""Recupera i documenti in _DaSmistare usando il modello VISION (legge le
immagini delle pagine). Utile per scansioni/libri che Tesseract non legge.

Garanzia: usa il LOCK unico (non gira mai insieme al daemon) e scarica il
modello TEXT prima di caricare il VISION -> i due modelli non sono MAI in RAM
insieme. A fine corsa scarica anche il vision.

Uso: ocr-vision-recover [--dry-run]
"""
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, ollama_mgr, vision
from ocrsys.locking import SingleInstanceLock, AlreadyRunning
from ocrsys.db import Database
from ocrsys.taxonomy import Taxonomy
from ocrsys.naming import build_name, dir_categoria, resolve_collision
from ocrsys.dates import normalize_date


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def _run(dry_run: bool):
    if not vision.disponibile():
        print("Manca 'pdftoppm' -> brew install poppler"); return
    ollama_mgr.ensure()
    if not ollama_mgr.is_up():
        print("Ollama non disponibile."); return
    # MAI due modelli insieme: scarica il TEXT prima di usare il VISION
    ollama_mgr.stop_modello(config.OLLAMA_MODEL)

    tax = Taxonomy.load(config.CATEGORIE_YAML)
    db = Database(config.DB_PATH)
    files = sorted(p for p in config.DA_SMISTARE.glob("*")
                   if p.is_file() and p.suffix.lower() in config.INPUT_EXTS)
    print(f"Vision-recover su {len(files)} documenti in _DaSmistare"
          f"{' (DRY-RUN)' if dry_run else ''}...\n")
    recuperati = 0
    try:
        mittenti = db.known_senders()
        for i, f in enumerate(files, 1):
            try:
                meta = vision.classifica(f, tax, mittenti)
                if not (meta.get("valido") and tax.is_valid(meta["categoria"])):
                    print(f"[{i}/{len(files)}] {f.name[:45]} -> resta _DaSmistare")
                    continue
                data = normalize_date(meta.get("data"))
                name = build_name(data, meta["mittente"], meta["tipo"],
                                  meta["dettaglio"])
                dest_dir = dir_categoria(config.ARCHIVIO, meta["categoria"],
                                         data, config.CATEGORIE_PER_ANNO)
                rel = str(dest_dir.relative_to(config.BASE) / name)
                print(f"[{i}/{len(files)}] {f.name[:40]} -> {rel}")
                if dry_run:
                    recuperati += 1
                    continue
                sha = _sha(f)
                dest_dir.mkdir(parents=True, exist_ok=True)
                name = resolve_collision(dest_dir, name)
                shutil.move(str(f), str(dest_dir / name))
                relpath = str((dest_dir / name).relative_to(config.BASE))
                campi = dict(
                    nome_file=name, percorso=relpath,
                    categoria=meta["categoria"],
                    data_documento=data or "0000-00-00",
                    mittente=meta.get("mittente", ""), tipo=meta.get("tipo", ""),
                    tags=" ".join(meta.get("tags") or []),
                    testo_completo=meta.get("testo", ""))
                # I file image-only finiti in _DaSmistare non hanno una riga in
                # DB (la pipeline non li indicizza): UPDATE non troverebbe nulla
                # e resterebbero invisibili alla ricerca -> inserisci se assenti.
                if db.already_processed(sha):
                    db.aggiorna_per_sha(sha, **campi)
                else:
                    db.insert({**campi, "sha256": sha, "confidenza": "vision"})
                recuperati += 1
            except Exception as e:
                print(f"[{i}/{len(files)}] {f.name[:40]} ERRORE: {str(e)[:50]}")
        if not dry_run and recuperati:
            db.rebuild_fts()    # riallinea l'indice ai testi/tag aggiornati
    finally:
        db.close()
        ollama_mgr.stop_modello(config.OLLAMA_VISION_MODEL)   # scarica il vision
    print(f"\nFatto. Recuperati: {recuperati}/{len(files)}")


def main():
    dry_run = "--dry-run" in sys.argv
    try:
        with SingleInstanceLock(config.LOCK_PATH):
            _run(dry_run)
    except AlreadyRunning:
        print("Un altro processo OCR e' in corso (daemon?). "
              "Ferma il daemon (ocr-auto-off) e riprova.")


if __name__ == "__main__":
    main()

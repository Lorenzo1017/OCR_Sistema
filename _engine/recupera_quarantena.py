"""Riprocessa i documenti finiti in quarantena (_DaSmistare/_errori) con la
pipeline standard. Utile dopo il fix "testo nativo": i PDF firmati/nativi che
ocrmypdf rifiutava ora vengono catalogati usando il testo gia' presente.

Uso: ocr-recupera [--dry-run]
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, ollama_mgr
from ocrsys.locking import SingleInstanceLock, AlreadyRunning
from ocrsys.pipeline import build_default_context, process_file


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def _run(dry_run: bool):
    quar = config.DA_SMISTARE_ERRORI
    files = sorted(p for p in quar.glob("*")
                   if p.is_file() and p.suffix.lower() in config.INPUT_EXTS)
    if not files:
        print("Nessun file in quarantena."); return
    print(f"Riprocesso {len(files)} documenti in quarantena"
          f"{' (DRY-RUN)' if dry_run else ''}...\n")
    if dry_run:
        for f in files:
            print(f"  - {f.name}")
        return

    proc = ollama_mgr.ensure()
    if not ollama_mgr.is_up():
        print("Ollama non disponibile."); return
    ctx = build_default_context()
    ok = resta = 0
    try:
        for i, f in enumerate(files, 1):
            try:
                sha = _sha(f)
                status = process_file(f, ctx)
                if status in ("ok", "skip"):
                    # catalogato (o gia' presente): togli riga errore + originale
                    ctx.db.conn.execute("DELETE FROM errori WHERE sha256=?", (sha,))
                    ctx.db.conn.commit()
                    f.unlink()
                    ok += 1
                    print(f"[{i}/{len(files)}] {f.name[:45]} -> catalogato")
                else:
                    resta += 1
                    print(f"[{i}/{len(files)}] {f.name[:45]} -> ancora _DaSmistare")
            except Exception as e:
                resta += 1
                print(f"[{i}/{len(files)}] {f.name[:45]} ERRORE: {str(e)[:50]}")
    finally:
        ctx.db.close()
        ollama_mgr.stop_model()
        ollama_mgr.stop_server(proc)
    print(f"\nFatto. Recuperati: {ok}/{len(files)} (restano {resta})")


def main():
    dry_run = "--dry-run" in sys.argv
    try:
        with SingleInstanceLock(config.LOCK_PATH):
            _run(dry_run)
    except AlreadyRunning:
        print("Un altro processo OCR e' in corso. Ferma il daemon (ocr-auto-off).")


if __name__ == "__main__":
    main()

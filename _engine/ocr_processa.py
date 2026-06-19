import csv
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.locking import SingleInstanceLock, AlreadyRunning
from ocrsys.pipeline import build_default_context, process_file


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _quarantena(f: Path):
    config.DA_SMISTARE_ERRORI.mkdir(parents=True, exist_ok=True)
    dest = config.DA_SMISTARE_ERRORI / f.name
    i = 2
    while dest.exists():
        dest = config.DA_SMISTARE_ERRORI / f"{f.stem}_v{i}{f.suffix}"
        i += 1
    shutil.move(str(f), str(dest))


def run():
    ctx = build_default_context()
    files = sorted(
        p for p in config.INBOX.iterdir()
        if p.suffix.lower() in config.INPUT_EXTS
    )
    if not files:
        print("Inbox vuota. Metti i documenti in:", config.INBOX)
        return

    print(f"Trovati {len(files)} documenti. Inizio...\n")
    ok = skip = dasmistare = errori = 0
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name} ... ", end="", flush=True)
        try:
            status = process_file(f, ctx)
            if status == "ok":
                ok += 1; print("OK")
            elif status == "skip":
                skip += 1; print("gia fatto (duplicato), rimuovo da inbox")
            else:
                dasmistare += 1; print("-> _DaSmistare")
            # rimuovi sempre l'originale dalla inbox: ok/dasmistare = archiviato
            # + backup in originali/; skip = duplicato gia' presente in archivio.
            f.unlink()
        except Exception as e:
            errori += 1
            with (config.LOG_ERRORI).open("a", newline="") as lf:
                csv.writer(lf).writerow([f.name, str(e)])
            # F3: dopo MAX_TENTATIVI fallimenti sullo stesso file -> quarantena,
            # cosi' un file "avvelenato" non viene ritentato all'infinito.
            try:
                tentativi = ctx.db.record_error(_sha256(f), f.name, str(e))
            except Exception:
                tentativi = 0
            if tentativi >= config.MAX_TENTATIVI:
                _quarantena(f)
                print(f"ERRORE (tentativo {tentativi}) -> quarantena _errori: {e}")
            else:
                print(f"ERRORE (tentativo {tentativi}/{config.MAX_TENTATIVI}), "
                      f"riprovo al prossimo giro: {e}")

    print(f"\nFatto. OK:{ok}  DaSmistare:{dasmistare}  "
          f"Saltati:{skip}  Errori:{errori}")
    if dasmistare:
        print(f"Controlla {config.DA_SMISTARE}")
    if errori:
        print(f"Errori in {config.LOG_ERRORI}")


def main():
    # F2: lock unico condiviso tra avvio manuale e watcher automatico.
    try:
        with SingleInstanceLock(config.LOCK_PATH):
            run()
    except AlreadyRunning:
        print("Un altro processo OCR e' gia' in corso. Esco.")


if __name__ == "__main__":
    main()

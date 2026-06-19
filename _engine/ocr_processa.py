import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.pipeline import build_default_context, process_file


def main():
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
                skip += 1; print("gia fatto, salto")
            else:
                dasmistare += 1; print("-> _DaSmistare")
            if status != "skip":
                f.unlink()
        except Exception as e:
            errori += 1
            print(f"ERRORE: {e}")
            with (config.LOG_ERRORI).open("a", newline="") as lf:
                csv.writer(lf).writerow([f.name, str(e)])

    print(f"\nFatto. OK:{ok}  DaSmistare:{dasmistare}  "
          f"Saltati:{skip}  Errori:{errori}")
    if dasmistare:
        print(f"Controlla {config.DA_SMISTARE}")
    if errori:
        print(f"Errori in {config.LOG_ERRORI}")


if __name__ == "__main__":
    main()

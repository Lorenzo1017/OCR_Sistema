"""Trova e risolve i documenti duplicati (stesso contenuto, byte diversi).
Di ogni gruppo tiene il piu' corposo e sposta gli altri in _Sistema/duplicati/.

Uso:
    ocr-duplicati            # elenca i duplicati SENZA toccare nulla (dry-run)
    ocr-duplicati --applica  # sposta i meno corposi in _Sistema/duplicati/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, dedup
from ocrsys.db import Database
from ocrsys.locking import SingleInstanceLock, AlreadyRunning


def _run(applica: bool):
    db = Database(config.DB_PATH)
    try:
        agg = dedup.backfill_firme(db)
        if agg:
            print(f"(calcolata la firma per {agg} documenti gia' presenti)\n")
        gruppi = dedup.gruppi_duplicati(db)
        if not gruppi:
            print("Nessun duplicato trovato."); return
        totale = 0
        for firma in gruppi:
            rows = sorted(
                db.conn.execute("SELECT * FROM documenti WHERE firma = ?",
                                (firma,)).fetchall(),
                key=dedup.corposita, reverse=True)
            tenuto, perdenti = rows[0], rows[1:]
            print(f"Duplicati ({len(rows)}): tengo «{tenuto['nome_file']}» "
                  f"({len(tenuto['testo_completo'] or '')} caratteri)")
            for r in perdenti:
                print(f"   - {'sposto' if applica else 'sposterei'}: "
                      f"{r['nome_file']} ({len(r['testo_completo'] or '')} car.)")
            totale += len(perdenti)
        if applica:
            mossi = dedup.dedup_tutto(db)
            print(f"\nFatto. Spostati in duplicati/: {mossi}")
        else:
            print(f"\nDuplicati da spostare: {totale}. "
                  f"Lancia 'ocr-duplicati --applica' per farlo "
                  f"(finiscono in _Sistema/duplicati/, reversibile).")
    finally:
        db.close()


def main():
    applica = "--applica" in sys.argv
    try:
        with SingleInstanceLock(config.LOCK_PATH):
            _run(applica)
    except AlreadyRunning:
        print("Un altro processo OCR e' in corso (daemon?). Riprova piu' tardi.")


if __name__ == "__main__":
    main()

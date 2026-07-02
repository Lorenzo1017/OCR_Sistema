"""Esportazioni dell'archivio. Output in <OCR_Sistema>/esportazioni/.

Uso:
    ocr-esporta indice                       # catalogo completo in CSV (Excel)
    ocr-esporta categoria "Salute/Referti"   # zip dei PDF della categoria
    ocr-esporta cerca "mutuo 2024"           # zip dei PDF che matchano la ricerca
    ocr-esporta backup                       # zip archivio+DB+configurazione
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, export
from ocrsys.db import Database

_USO = __doc__.split("Uso:")[1]


def main():
    if len(sys.argv) < 2:
        print("Uso:" + _USO)
        return
    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "backup":
        print("Creo il backup completo (puo' volerci qualche minuto)...")
        dest = export.backup_completo()
        mb = dest.stat().st_size / 1_000_000
        print(f"Backup: {dest}  ({mb:.0f} MB)")
        return

    db = Database(config.DB_PATH)
    try:
        if cmd == "indice":
            dest = export.indice_csv(db)
            print(f"Indice CSV: {dest}")
        elif cmd == "categoria" and arg:
            dest, agg, man = export.zip_categoria(db, arg)
            if dest is None:
                print(f"Nessun documento nella categoria '{arg}'.")
            else:
                print(f"Zip: {dest}  ({agg} PDF" +
                      (f", {man} mancanti su disco" if man else "") + ")")
        elif cmd == "cerca" and arg:
            dest, agg, man = export.zip_ricerca(db, arg)
            if dest is None:
                print(f"Nessun risultato per '{arg}'.")
            else:
                print(f"Zip: {dest}  ({agg} PDF" +
                      (f", {man} mancanti su disco" if man else "") + ")")
        else:
            print("Uso:" + _USO)
    finally:
        db.close()


if __name__ == "__main__":
    main()

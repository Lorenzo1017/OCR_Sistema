"""Controlla la coerenza tra l'indice (DB) e i file in archivio.
Uso: python verifica_db.py [--fix]
  --fix  rimuove dal DB le righe orfane (file non piu' presenti)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database


def main():
    d = Database(config.DB_PATH)
    rows = list(d.conn.execute("SELECT id, percorso FROM documenti"))
    in_db = {r["percorso"] for r in rows}

    orfani = [(r["id"], r["percorso"]) for r in rows
              if not (config.BASE / r["percorso"]).exists()]

    su_disco = [p for p in config.ARCHIVIO.rglob("*")
                if p.is_file() and p.suffix.lower() == ".pdf"]
    non_indicizzati = [p for p in su_disco
                       if str(p.relative_to(config.BASE)) not in in_db]

    print("=" * 50)
    print(" Coerenza DB <-> archivio")
    print("=" * 50)
    print(f"Documenti nel DB        : {len(rows)}")
    print(f"PDF in archivio         : {len(su_disco)}")
    print(f"Righe orfane (file mancante): {len(orfani)}")
    for _id, p in orfani[:15]:
        print(f"   [X] {p}")
    if len(orfani) > 15:
        print(f"   ...e altre {len(orfani) - 15}")
    print(f"File non indicizzati (in archivio, non nel DB): {len(non_indicizzati)}")
    for p in non_indicizzati[:15]:
        print(f"   [?] {p.relative_to(config.BASE)}")

    if "--fix" in sys.argv and orfani:
        d.conn.executemany("DELETE FROM documenti WHERE id = ?",
                            [(i,) for i, _ in orfani])
        d.conn.commit()
        print(f"\nRimosse {len(orfani)} righe orfane dal DB.")
    elif orfani:
        print("\n(usa --fix per rimuovere le righe orfane)")
    if not orfani and not non_indicizzati:
        print("\nTutto coerente.")
    d.close()


if __name__ == "__main__":
    main()

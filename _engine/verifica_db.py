"""Controlla la coerenza tra l'indice (DB) e i file in archivio.
Uso: python verifica_db.py [--fix]
  --fix  riconcilia: rimuove le righe orfane (file mancante) E indicizza i file
         in archivio non ancora nel DB (metadati dedotti dal nome/percorso)."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database
from ocrsys.naming import strip_anno


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def _indicizza(db: Database, p: Path) -> bool:
    """Inserisce nel DB un file di archivio non indicizzato, deducendo i
    metadati dal nome AAAA-MM-GG_Mittente_Tipo_Dettaglio e dalla categoria
    (cartelle sotto archivio/). Ritorna True se inserito."""
    cat = strip_anno(str(p.parent.relative_to(config.ARCHIVIO)))
    parti = p.stem.split("_")
    data = parti[0] if parti and len(parti[0]) == 10 and parti[0][4] == "-" else "0000-00-00"
    mitt = parti[1].replace("-", " ") if len(parti) > 1 else ""
    tipo = parti[2] if len(parti) > 2 else ""
    det = " ".join(parti[3:]).replace("-", " ") if len(parti) > 3 else ""
    return db.insert({
        "nome_file": p.name, "percorso": str(p.relative_to(config.BASE)),
        "categoria": cat, "data_documento": data, "mittente": mitt,
        "tipo": tipo, "tags": "", "testo_completo": det, "n_pagine": 0,
        "confidenza": "reindex", "sha256": _sha(p)})


def analizza(db: Database):
    """Ritorna (orfani, non_indicizzati, n_righe, n_disco) senza modificare nulla."""
    rows = list(db.conn.execute("SELECT id, percorso FROM documenti"))
    in_db = {r["percorso"] for r in rows}
    orfani = [(r["id"], r["percorso"]) for r in rows
              if not (config.BASE / r["percorso"]).exists()]
    su_disco = [p for p in config.ARCHIVIO.rglob("*")
                if p.is_file() and p.suffix.lower() == ".pdf"]
    non_indicizzati = [p for p in su_disco
                       if str(p.relative_to(config.BASE)) not in in_db]
    return orfani, non_indicizzati, len(rows), len(su_disco)


def riconcilia(db: Database) -> tuple:
    """Rimuove le righe orfane e indicizza i file mancanti. Ritorna
    (rimosse, aggiunte). Usato da ocr-check-db --fix e dalla manutenzione."""
    orfani, non_indicizzati, _, _ = analizza(db)
    if orfani:
        db.conn.executemany("DELETE FROM documenti WHERE id = ?",
                            [(i,) for i, _ in orfani])
        db.conn.commit()
    aggiunti = sum(1 for p in non_indicizzati if _indicizza(db, p))
    if aggiunti:
        db.rebuild_fts()
    return len(orfani), aggiunti


def main():
    d = Database(config.DB_PATH)
    orfani, non_indicizzati, n_righe, n_disco = analizza(d)

    print("=" * 50)
    print(" Coerenza DB <-> archivio")
    print("=" * 50)
    print(f"Documenti nel DB        : {n_righe}")
    print(f"PDF in archivio         : {n_disco}")
    print(f"Righe orfane (file mancante): {len(orfani)}")
    for _id, p in orfani[:15]:
        print(f"   [X] {p}")
    if len(orfani) > 15:
        print(f"   ...e altre {len(orfani) - 15}")
    print(f"File non indicizzati (in archivio, non nel DB): {len(non_indicizzati)}")
    for p in non_indicizzati[:15]:
        print(f"   [?] {p.relative_to(config.BASE)}")

    if "--fix" in sys.argv:
        rimosse, aggiunti = riconcilia(d)
        if rimosse:
            print(f"\nRimosse {rimosse} righe orfane dal DB.")
        if aggiunti:
            print(f"Indicizzati {aggiunti} file che mancavano nel DB.")
        if not rimosse and not aggiunti:
            print("\nNiente da correggere.")
    else:
        if orfani or non_indicizzati:
            print("\n(usa --fix per riconciliare: pulire orfane + indicizzare mancanti)")
        else:
            print("\nTutto coerente.")
    d.close()


if __name__ == "__main__":
    main()

"""Report sulla salute dell'archivio: volume, qualita' dei metadati, quarantena,
distribuzione categorie. Uso: ocr-stato
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database


def _pct(n, tot):
    return f"{100 * n // tot}%" if tot else "0%"


def main():
    db = Database(config.DB_PATH)
    c = db.conn
    tot = c.execute("SELECT COUNT(*) FROM documenti").fetchone()[0]
    arch = sum(1 for _, _, fs in os.walk(config.ARCHIVIO)
               for f in fs if f.lower().endswith(".pdf"))
    ds = len([p for p in config.DA_SMISTARE.glob("*")
              if p.is_file() and p.suffix.lower() in config.INPUT_EXTS])
    quar = 0
    if config.DA_SMISTARE_ERRORI.exists():
        quar = len([p for p in config.DA_SMISTARE_ERRORI.glob("*")
                    if p.is_file() and p.suffix.lower() in config.INPUT_EXTS])

    print("=== ARCHIVIO OCR — STATO ===\n")
    print(f"Documenti catalogati : {tot}")
    print(f"File in archivio      : {arch}")
    print(f"Da smistare           : {ds}")
    print(f"In quarantena (errori): {quar}")

    print("\n--- Qualita' metadati ---")
    nodate = c.execute("SELECT COUNT(*) FROM documenti WHERE data_documento IN "
                       "('0000-00-00','') OR data_documento IS NULL").fetchone()[0]
    nomitt = c.execute("SELECT COUNT(*) FROM documenti WHERE mittente IN "
                       "('','Ignoto','ANONIMO') OR mittente IS NULL").fetchone()[0]
    notag = c.execute("SELECT COUNT(*) FROM documenti WHERE tags IS NULL OR "
                      "tags=''").fetchone()[0]
    notext = c.execute("SELECT COUNT(*) FROM documenti WHERE "
                       "LENGTH(COALESCE(testo_completo,''))<30").fetchone()[0]
    print(f"senza data     : {nodate} ({_pct(nodate, tot)})")
    print(f"mittente ignoto: {nomitt} ({_pct(nomitt, tot)})")
    print(f"senza tag      : {notag} ({_pct(notag, tot)})")
    print(f"testo scarso   : {notext} ({_pct(notext, tot)})")

    print("\n--- Righe DB orfane (file mancante) ---")
    orfane = sum(1 for (p,) in c.execute("SELECT percorso FROM documenti")
                 if not p or not (config.BASE / p).exists())
    print(f"orfane: {orfane}" + ("  (esegui ocr-check-db per pulire)" if orfane else "  ok"))

    print("\n--- Categorie (tutte, per numero) ---")
    for cat, n in c.execute("SELECT categoria, COUNT(*) n FROM documenti "
                            "GROUP BY categoria ORDER BY n DESC"):
        print(f"  {n:4}  {cat}")
    db.close()


if __name__ == "__main__":
    main()

"""Deduplica per CONTENUTO: due documenti con lo stesso testo (anche se i byte
del PDF differiscono: riscansione, ri-esportazione) hanno la stessa 'firma'.
Di un gruppo di duplicati si tiene il piu' CORPOSO (piu' testo estratto, poi piu'
pagine, poi file piu' grande) e gli altri vengono SPOSTATI in _Sistema/duplicati/
(reversibile) e tolti dal DB.

La firma e' lo sha256 del testo normalizzato in modo aggressivo (solo lettere e
numeri, minuscolo, senza spazi): assorbe differenze di punteggiatura/spaziatura
dell'OCR. Documenti con pochissimo testo NON ottengono firma (troppo rischioso
dichiararli uguali)."""
import hashlib
import re

from . import config
from .naming import resolve_collision

_SOLO_ALNUM = re.compile(r"[^0-9a-zà-ÿ]+", re.IGNORECASE)
# Sotto questa lunghezza di testo NON si fa firma: documenti image-only con poca
# trascrizione (es. "Esame di laboratorio per X") sono generici e IDENTICI tra
# documenti DIVERSI -> dichiararli duplicati cancellerebbe file reali. Serve
# testo sostanzioso per essere sicuri che due documenti siano lo stesso.
_MIN_ALNUM = 300


def firma_testo(testo: str) -> str:
    """sha256 del testo normalizzato (alfanumerico, minuscolo, senza spazi).
    Stringa vuota se il testo e' troppo scarso per dichiarare un'uguaglianza."""
    if not testo:
        return ""
    norm = _SOLO_ALNUM.sub("", testo.lower())
    if len(norm) < _MIN_ALNUM:
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _dim_file(percorso: str) -> int:
    try:
        return (config.BASE / percorso).stat().st_size
    except OSError:
        return 0


def corposita(row) -> tuple:
    """Chiave d'ordine: (lunghezza testo, n_pagine, dimensione file). Il massimo
    e' il documento 'piu' corposo' da tenere."""
    testo = row["testo_completo"] or ""
    pagine = row["n_pagine"] or 0
    return (len(testo), pagine, _dim_file(row["percorso"]))


def backfill_firme(db) -> int:
    """(Ri)calcola la firma di TUTTI i documenti dal loro testo. Ricalcolare
    sempre (e' solo hashing, millisecondi) fa si' che un eventuale cambio di
    soglia si propaghi, senza firme 'vecchie' rimaste in giro. Ritorna quante
    righe aggiornate (firma cambiata)."""
    rows = db.conn.execute(
        "SELECT sha256, testo_completo, firma FROM documenti").fetchall()
    n = 0
    for sha, testo, vecchia in rows:
        f = firma_testo(testo or "")
        if f != (vecchia or ""):
            db.conn.execute("UPDATE documenti SET firma = ? WHERE sha256 = ?",
                            (f, sha))
            n += 1
    if n:
        db.conn.commit()
    return n


def _sposta_in_duplicati(db, row) -> bool:
    """Sposta il file del duplicato in _Sistema/duplicati/ e ne toglie la riga
    dal DB. Ritorna True se fatto."""
    src = config.BASE / row["percorso"]
    config.DUPLICATI.mkdir(parents=True, exist_ok=True)
    try:
        if src.exists():
            nome = resolve_collision(config.DUPLICATI, row["nome_file"])
            src.rename(config.DUPLICATI / nome)
        db.conn.execute("DELETE FROM documenti WHERE sha256 = ?",
                        (row["sha256"],))
        db.conn.commit()
        return True
    except OSError:
        return False


def risolvi_gruppo(db, firma: str, stampa=False) -> int:
    """Di tutti i documenti con questa firma tiene il piu' corposo e sposta gli
    altri in duplicati/. Ritorna quanti spostati."""
    if not firma:
        return 0
    rows = db.conn.execute(
        "SELECT * FROM documenti WHERE firma = ?", (firma,)).fetchall()
    if len(rows) < 2:
        return 0
    rows = sorted(rows, key=corposita, reverse=True)
    tenuto, perdenti = rows[0], rows[1:]
    mossi = 0
    for r in perdenti:
        if _sposta_in_duplicati(db, r):
            mossi += 1
            if stampa:
                print(f"  duplicato -> duplicati/: {r['nome_file']}\n"
                      f"     (tengo: {tenuto['nome_file']})")
    return mossi


def gruppi_duplicati(db) -> list:
    """Ritorna le firme che hanno piu' di un documento (per report/dry-run)."""
    return [r[0] for r in db.conn.execute(
        "SELECT firma FROM documenti WHERE firma IS NOT NULL AND firma <> '' "
        "GROUP BY firma HAVING COUNT(*) > 1")]


def dedup_tutto(db, stampa=False) -> int:
    """Backfill firme + risolve tutti i gruppi di duplicati. Ritorna quanti
    documenti spostati in duplicati/. Ricostruisce l'indice FTS alla fine."""
    backfill_firme(db)
    mossi = 0
    for firma in gruppi_duplicati(db):
        mossi += risolvi_gruppo(db, firma, stampa=stampa)
    if mossi:
        db.rebuild_fts()   # le DELETE non passano dai trigger FTS
    return mossi

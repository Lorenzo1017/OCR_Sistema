"""Ricerca semantica locale: embedding dei documenti con nomic-embed-text
(~274MB via Ollama) + similarita' coseno. Complementare alla ricerca FTS:
trova "spese dentista" anche se il documento dice "odontoiatra".

Tabella embeddings nel DB principale: (sha256, vec) con il vettore serializzato
in float32. 1300 doc x 768 dim -> ~4MB, confronto brute-force in millisecondi.
"""
import array
import json
import urllib.request

from . import config

MODELLO = "nomic-embed-text"
_URL_EMBED = "http://localhost:11434/api/embeddings"
_MAX_TESTO = 2000     # bastano le prime ~300 parole per il "tema" del documento

_SCHEMA = """
CREATE TABLE IF NOT EXISTS embeddings (
    sha256 TEXT PRIMARY KEY,
    vec BLOB NOT NULL
);
"""


def _assicura_tabella(db):
    db.conn.executescript(_SCHEMA)
    db.conn.commit()


def embed(testo: str) -> list:
    """Vettore embedding del testo (richiede Ollama su + modello scaricato)."""
    payload = json.dumps({"model": MODELLO,
                          "prompt": testo[:_MAX_TESTO]}).encode()
    req = urllib.request.Request(_URL_EMBED, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read()).get("embedding") or []


def _serializza(vec) -> bytes:
    return array.array("f", vec).tobytes()


def _deserializza(blob: bytes) -> array.array:
    a = array.array("f")
    a.frombytes(blob)
    return a


def _coseno(a, b) -> float:
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


def indicizza(db, stampa=False) -> int:
    """Calcola gli embedding per i documenti che non li hanno ancora.
    Ritorna quanti indicizzati. Idempotente."""
    _assicura_tabella(db)
    rows = db.conn.execute(
        "SELECT d.sha256, d.mittente, d.tipo, d.tags, d.testo_completo "
        "FROM documenti d LEFT JOIN embeddings e ON e.sha256 = d.sha256 "
        "WHERE e.sha256 IS NULL "
        "AND LENGTH(COALESCE(d.testo_completo,'')) > 30").fetchall()
    fatti = 0
    for i, (sha, mitt, tipo, tags, testo) in enumerate(rows, 1):
        # mittente/tipo/tags in testa: pesano di piu' nel vettore
        contesto = f"{mitt} {tipo} {tags}\n{testo}"
        try:
            vec = embed(contesto)
        except Exception as e:
            if stampa:
                print(f"[{i}/{len(rows)}] errore embed: {str(e)[:50]}")
            continue
        if vec:
            db.conn.execute(
                "INSERT OR REPLACE INTO embeddings (sha256, vec) VALUES (?,?)",
                (sha, _serializza(vec)))
            fatti += 1
            if stampa and fatti % 50 == 0:
                print(f"[{i}/{len(rows)}] indicizzati {fatti}")
    db.conn.commit()
    return fatti


def cerca(db, query: str, k: int = 20) -> list:
    """Top-k documenti per similarita' semantica. Ritorna dict di documenti
    con in piu' 'punteggio'. Lista vuota se l'indice non esiste ancora."""
    _assicura_tabella(db)
    try:
        qv = embed(query)
    except Exception:
        return []
    if not qv:
        return []
    punteggi = []
    for sha, blob in db.conn.execute("SELECT sha256, vec FROM embeddings"):
        punteggi.append((_coseno(qv, _deserializza(blob)), sha))
    punteggi.sort(reverse=True)
    out = []
    for score, sha in punteggi[:k]:
        r = db.conn.execute("SELECT * FROM documenti WHERE sha256=?",
                            (sha,)).fetchone()
        if r:
            d = dict(r)
            d["punteggio"] = round(score, 3)
            out.append(d)
    return out

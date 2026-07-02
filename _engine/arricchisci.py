"""Arricchisce i metadati dei documenti gia' archiviati: per quelli senza tag
o con mittente ignoto (ma con testo), chiede al LLM SOLO i campi mancanti.
Non sposta file: aggiorna DB + indice di ricerca.

Uso: ocr-arricchisci [--dry-run] [--limite N]
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, ollama_mgr
from ocrsys.locking import SingleInstanceLock, AlreadyRunning
from ocrsys.db import Database

_PROMPT = """Sei un archivista. Dal testo del documento ricava i campi richiesti.
Rispondi SOLO con JSON: {"mittente":"chi emette il documento","tags":["3-6 parole chiave"]}
Se il mittente non e' deducibile usa "".

TESTO:
{testo}

JSON:"""

_IGNOTI = ("", "Ignoto", "ANONIMO", "Sconosciuto")


def _chiedi(testo: str) -> dict:
    payload = json.dumps({
        "model": config.OLLAMA_MODEL,
        "prompt": _PROMPT.replace("{testo}", testo[:4000]),
        "stream": False, "format": "json",
        "keep_alive": config.OLLAMA_KEEP_ALIVE,
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(config.OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = json.loads(r.read()).get("response", "")
    try:
        d = json.loads(raw)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _norm_tags(tags) -> str:
    if not isinstance(tags, list):
        return ""
    visti = []
    for t in tags:
        s = str(t).strip().lower()
        if s and s not in visti:
            visti.append(s)
    return " ".join(visti[:8])


def _run(dry: bool, limite: int):
    db = Database(config.DB_PATH)
    rows = db.conn.execute(
        "SELECT sha256, nome_file, mittente, tags, testo_completo FROM documenti "
        "WHERE (tags IS NULL OR tags='' OR mittente IN (?,?,?,?)) "
        "AND LENGTH(COALESCE(testo_completo,'')) > 50", _IGNOTI).fetchall()
    if limite:
        rows = rows[:limite]
    print(f"Da arricchire: {len(rows)} documenti{' (DRY-RUN)' if dry else ''}\n")
    if not rows:
        db.close(); return
    if not dry:
        ollama_mgr.ensure()
        if not ollama_mgr.is_up():
            print("Ollama non disponibile."); db.close(); return
    fatti = 0
    try:
        for i, (sha, nome, mitt, tags, testo) in enumerate(rows, 1):
            if dry:
                manca = []
                if not tags: manca.append("tags")
                if (mitt or "") in _IGNOTI: manca.append("mittente")
                print(f"[{i}/{len(rows)}] {nome[:55]} -> manca: {','.join(manca)}")
                continue
            try:
                d = _chiedi(testo)
            except Exception as e:
                print(f"[{i}/{len(rows)}] {nome[:45]} ERRORE: {str(e)[:40]}")
                continue
            campi = {}
            if not tags:
                nt = _norm_tags(d.get("tags"))
                if nt: campi["tags"] = nt
            if (mitt or "") in _IGNOTI:
                nm = str(d.get("mittente", "")).strip()
                if nm and nm not in _IGNOTI: campi["mittente"] = nm
            if campi:
                db.aggiorna_per_sha(sha, **campi)
                fatti += 1
                print(f"[{i}/{len(rows)}] {nome[:45]} + {', '.join(campi)}")
            else:
                print(f"[{i}/{len(rows)}] {nome[:45]} (niente di utile)")
        if not dry and fatti:
            db.rebuild_fts()
    finally:
        db.close()
        if not dry:
            ollama_mgr.stop_model()
    print(f"\nArricchiti: {fatti}/{len(rows)}")


def main():
    dry = "--dry-run" in sys.argv
    limite = 0
    if "--limite" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--limite") + 1])
    try:
        with SingleInstanceLock(config.LOCK_PATH):
            _run(dry, limite)
    except AlreadyRunning:
        print("Un altro processo OCR e' in corso (daemon?). Riprova piu' tardi.")


if __name__ == "__main__":
    main()

"""Costruisce/aggiorna l'indice semantico (embedding) dei documenti.
Da rilanciare ogni tanto per includere i documenti nuovi (idempotente).
Uso: ocr-indicizza
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, ollama_mgr, semantic
from ocrsys.db import Database


def main():
    ollama_mgr.ensure()
    if not ollama_mgr.is_up():
        print("Ollama non disponibile."); return
    db = Database(config.DB_PATH)
    try:
        n = semantic.indicizza(db, stampa=True)
        tot = db.conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        print(f"Indicizzati ora: {n} | totale nell'indice semantico: {tot}")
    finally:
        db.close()
        ollama_mgr.stop_modello(semantic.MODELLO)


if __name__ == "__main__":
    main()

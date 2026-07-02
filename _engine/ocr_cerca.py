"""Ricerca nell'archivio.
Uso:
    ocr-cerca "parole da cercare"                # full-text (FTS)
    ocr-cerca --semantica "spese dal dentista"   # per significato (embedding)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database


def main():
    args = sys.argv[1:]
    semantica = "--semantica" in args
    args = [a for a in args if a != "--semantica"]
    if not args:
        print('Uso: ocr-cerca [--semantica] "parole da cercare"')
        return
    query = " ".join(args)
    db = Database(config.DB_PATH)
    try:
        if semantica:
            from ocrsys import ollama_mgr, semantic
            ollama_mgr.ensure()
            results = semantic.cerca(db, query)
            if not results:
                print("Nessun risultato (indice semantico vuoto? "
                      "esegui prima: ocr-indicizza)")
                return
        else:
            results = db.search(query)
            if not results:
                print("Nessun documento trovato.")
                return
        print(f"{len(results)} risultati:\n")
        for r in results:
            punt = f"  ~{r['punteggio']}" if semantica else ""
            print(f"  {r['data_documento']}  [{r['categoria']}]{punt}")
            print(f"     {r['nome_file']}")
            tags = (r.get('tags') or "").strip() if isinstance(r, dict) else \
                   ((r['tags'] or "").strip() if 'tags' in r.keys() else "")
            if tags:
                print(f"     tag: {tags}")
            print(f"     {config.BASE / r['percorso']}\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database


def main():
    if len(sys.argv) < 2:
        print('Uso: ocr-cerca "parole da cercare"')
        return
    query = " ".join(sys.argv[1:])
    db = Database(config.DB_PATH)
    results = db.search(query)
    if not results:
        print("Nessun documento trovato.")
        return
    print(f"{len(results)} risultati:\n")
    for r in results:
        print(f"  {r['data_documento']}  [{r['categoria']}]")
        print(f"     {r['nome_file']}")
        tags = (r['tags'] or "").strip() if 'tags' in r.keys() else ""
        if tags:
            print(f"     tag: {tags}")
        print(f"     {config.BASE / r['percorso']}\n")


if __name__ == "__main__":
    main()

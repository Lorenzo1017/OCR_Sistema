"""Sposta un documento gia' archiviato in un'altra categoria, correggendo anche
il DB e l'indice. Utile quando la classificazione automatica ha sbagliato.

Uso:
    ocr-sposta "parte del nome"  "Categoria/Sottocategoria"
    ocr-sposta --lista                      # elenca le categorie valide
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database
from ocrsys.taxonomy import Taxonomy
from ocrsys.naming import dir_categoria, resolve_collision


def _trova(db, frammento: str) -> list:
    cur = db.conn.execute(
        "SELECT sha256, nome_file, percorso, categoria, data_documento "
        "FROM documenti WHERE nome_file LIKE ? ORDER BY nome_file",
        (f"%{frammento}%",))
    return cur.fetchall()


def main():
    args = [a for a in sys.argv[1:]]
    tax = Taxonomy.load(config.CATEGORIE_YAML)
    if not args or args[0] == "--lista":
        print("Categorie valide:")
        for c in sorted(tax.valid_paths()):
            print("  ", c)
        return
    if len(args) < 2:
        print('Uso: ocr-sposta "parte del nome" "Categoria/Sottocategoria"')
        return
    frammento, categoria = args[0], args[1].strip("/")
    if not tax.is_valid(categoria):
        print(f"Categoria non valida: '{categoria}'. Usa: ocr-sposta --lista")
        return

    db = Database(config.DB_PATH)
    try:
        trovati = _trova(db, frammento)
        if not trovati:
            print(f"Nessun documento con '{frammento}' nel nome.")
            return
        if len(trovati) > 1:
            print(f"Trovati {len(trovati)} documenti, sii piu' specifico:")
            for _, nome, _, cat, _ in trovati[:20]:
                print(f"  [{cat}] {nome}")
            return
        sha, nome, percorso, cat_vecchia, data_doc = trovati[0]
        src = config.BASE / percorso
        if not src.exists():
            print(f"File non trovato su disco: {percorso}")
            return
        if cat_vecchia == categoria:
            print("Il documento e' gia' in quella categoria.")
            return
        # rispetta l'eventuale sottocartella-anno della categoria di arrivo
        dest_dir = dir_categoria(config.ARCHIVIO, categoria, data_doc,
                                 config.CATEGORIE_PER_ANNO)
        dest_dir.mkdir(parents=True, exist_ok=True)
        nuovo_nome = resolve_collision(dest_dir, nome)
        dest = dest_dir / nuovo_nome
        src.rename(dest)
        relpath = str(dest.relative_to(config.BASE))
        db.aggiorna_per_sha(sha, categoria=categoria, percorso=relpath,
                            nome_file=nuovo_nome)
        print(f"Spostato:\n  {cat_vecchia} -> {categoria}\n  {nome}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

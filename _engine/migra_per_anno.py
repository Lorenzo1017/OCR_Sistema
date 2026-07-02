"""Migrazione one-time: sposta i documenti delle categorie 'per anno'
(config.CATEGORIE_PER_ANNO) nelle sottocartelle <AAAA> in base alla data,
aggiornando il percorso nel DB. Idempotente: i file gia' nella cartella
giusta non vengono toccati. Uso: python migra_per_anno.py [--dry-run]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database
from ocrsys.naming import dir_categoria, resolve_collision


def main():
    dry = "--dry-run" in sys.argv
    db = Database(config.DB_PATH)
    spostati = 0
    try:
        for cat in config.CATEGORIE_PER_ANNO:
            rows = db.conn.execute(
                "SELECT sha256, nome_file, percorso, data_documento "
                "FROM documenti WHERE categoria = ?", (cat,)).fetchall()
            print(f"{cat}: {len(rows)} documenti")
            for sha, nome, percorso, data in rows:
                src = config.BASE / percorso
                dest_dir = dir_categoria(config.ARCHIVIO, cat, data,
                                         config.CATEGORIE_PER_ANNO)
                if not src.exists():
                    print(f"  manca su disco, salto: {percorso}")
                    continue
                if src.parent == dest_dir:
                    continue        # gia' a posto
                if dry:
                    print(f"  {nome[:60]} -> {dest_dir.relative_to(config.BASE)}/")
                    spostati += 1
                    continue
                dest_dir.mkdir(parents=True, exist_ok=True)
                nuovo = resolve_collision(dest_dir, nome)
                src.rename(dest_dir / nuovo)
                db.aggiorna_per_sha(
                    sha, nome_file=nuovo,
                    percorso=str((dest_dir / nuovo).relative_to(config.BASE)))
                spostati += 1
    finally:
        db.close()
    print(f"\n{'Da spostare' if dry else 'Spostati'}: {spostati}")


if __name__ == "__main__":
    main()

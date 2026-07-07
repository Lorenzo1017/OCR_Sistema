"""Manutenzione notturna, tutto in un colpo (LaunchAgent com.ocrsistema.manutenzione):
  1. backup consistente del DB + configurazione (con rotazione)
  2. riconciliazione DB <-> archivio (rimuove orfane, indicizza mancanti)
  3. aggiornamento dell'indice semantico per i documenti nuovi (se disponibile)

Robusto: ogni passo e' isolato in try/except, un fallimento non blocca gli altri.
Uso manuale: ocr-manutenzione
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.db import Database

import backup_db
import verifica_db


def main():
    # 1) backup del DB (indipendente da tutto il resto)
    try:
        dest = backup_db.esegui(tieni=7)
        print(f"[backup] {dest.name}")
    except Exception as e:
        print(f"[backup] ERRORE: {str(e)[:80]}")

    db = Database(config.DB_PATH)
    try:
        # 2) riconciliazione DB <-> archivio
        try:
            rimosse, aggiunte = verifica_db.riconcilia(db)
            print(f"[riconcilia] orfane rimosse: {rimosse}, indicizzate: {aggiunte}")
        except Exception as e:
            print(f"[riconcilia] ERRORE: {str(e)[:80]}")

        # 3) indice semantico dei documenti nuovi (solo se Ollama + modello ok)
        try:
            from ocrsys import ollama_mgr, semantic
            ollama_mgr.ensure()
            if ollama_mgr.is_up():
                n = semantic.indicizza(db)
                print(f"[semantica] nuovi documenti indicizzati: {n}")
                ollama_mgr.stop_modello(semantic.MODELLO)
            else:
                print("[semantica] Ollama non disponibile, salto")
        except Exception as e:
            print(f"[semantica] ERRORE: {str(e)[:80]}")
    finally:
        db.close()
    print("Manutenzione completata.")


if __name__ == "__main__":
    main()

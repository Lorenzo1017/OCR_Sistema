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

import arricchisci
import backup_db
import verifica_db
from ocrsys.locking import SingleInstanceLock, AlreadyRunning


def _lavoro_db():
    db = Database(config.DB_PATH)
    try:
        # 2) riconciliazione DB <-> archivio
        try:
            rimosse, aggiunte = verifica_db.riconcilia(db)
            print(f"[riconcilia] orfane rimosse: {rimosse}, indicizzate: {aggiunte}")
        except Exception as e:
            print(f"[riconcilia] ERRORE: {str(e)[:80]}")

        # 2b) deduplica per contenuto: tiene il piu' corposo, sposta gli altri
        try:
            from ocrsys import dedup
            mossi = dedup.dedup_tutto(db)
            print(f"[dedup] duplicati spostati in duplicati/: {mossi}")
        except Exception as e:
            print(f"[dedup] ERRORE: {str(e)[:80]}")

        from ocrsys import ollama_mgr, semantic
        ollama_mgr.ensure()
        if not ollama_mgr.is_up():
            print("[llm] Ollama non disponibile, salto arricchimento+semantica")
        else:
            # 3) arricchimento metadati mancanti (tag/mittente) sui doc nuovi
            try:
                n = arricchisci.esegui(db, limite=300)
                print(f"[arricchisci] metadati completati su: {n} documenti")
            except Exception as e:
                print(f"[arricchisci] ERRORE: {str(e)[:80]}")
            finally:
                ollama_mgr.stop_model()   # scarica il text prima dell'embed
            # 4) indice semantico dei documenti nuovi
            try:
                n = semantic.indicizza(db)
                print(f"[semantica] nuovi documenti indicizzati: {n}")
                ollama_mgr.stop_modello(semantic.MODELLO)
            except Exception as e:
                print(f"[semantica] ERRORE: {str(e)[:80]}")
    finally:
        db.close()


def main():
    # 1) backup del DB: snapshot consistente via API SQLite, sicuro anche se il
    #    daemon sta scrivendo -> NON serve il lock.
    try:
        dest = backup_db.esegui(tieni=7)
        print(f"[backup] {dest.name}")
    except Exception as e:
        print(f"[backup] ERRORE: {str(e)[:80]}")
    # 2) il resto (riconcilia/dedup/arricchisci/semantica) MODIFICA il DB e
    #    l'indice FTS: prende il lock unico per non girare insieme al daemon
    #    (rebuild_fts concorrenti corromperebbero l'indice).
    try:
        with SingleInstanceLock(config.LOCK_PATH):
            _lavoro_db()
    except AlreadyRunning:
        print("[manutenzione] daemon occupato: rimando il lavoro DB al prossimo giro.")
        return
    print("Manutenzione completata.")


if __name__ == "__main__":
    main()

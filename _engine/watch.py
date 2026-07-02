"""Watcher cross-platform: controlla la inbox a intervalli regolari e processa
i documenti. Funziona identico su macOS, Linux e Windows (nessun bash/launchd).
Avvialo all'accensione tramite il meccanismo del tuo OS (vedi
README_PORTABILITA.md). Resta in esecuzione e dorme tra un giro e l'altro;
Ollama viene avviato solo quando ci sono file e fermato a fine batch."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, email_fetch
from ocrsys.runner import run_once

_MAX_LOG = 1_000_000   # 1 MB: sopra questa taglia il log viene dimezzato


def _ruota_log():
    """Tiene i log sotto controllo: se superano 1MB ne conserva solo la
    seconda meta' (le righe piu' recenti). Nessuna dipendenza, cross-OS."""
    nomi = ("log_auto.txt", "log_web.txt", "log_email.txt", "log_errori.csv")
    for nome in nomi:
        p = config.SISTEMA / nome
        try:
            if p.exists() and p.stat().st_size > _MAX_LOG:
                dati = p.read_bytes()[-_MAX_LOG // 2:]
                # riparti da una riga intera, non da meta' riga
                taglio = dati.find(b"\n") + 1
                p.write_bytes(b"[...log ruotato...]\n" + dati[taglio:])
        except OSError:
            pass


def main():
    while True:
        try:
            _ruota_log()
            # scarica prima gli allegati PDF dalle email etichettate (no-op se
            # non configurato), poi processa la inbox come sempre.
            email_fetch.scarica(stampa=False)
            # niente stampa (gira in background); le notifiche avvisano l'utente
            run_once(stampa=False, notifiche=True)
        except Exception as e:
            try:
                with config.LOG_ERRORI.open("a") as f:
                    f.write(f"watch loop error: {e}\n")
            except Exception:
                pass
        time.sleep(config.WATCH_INTERVAL)


if __name__ == "__main__":
    main()

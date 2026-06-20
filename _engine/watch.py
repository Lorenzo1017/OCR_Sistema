"""Watcher cross-platform: controlla la inbox a intervalli regolari e processa
i documenti. Funziona identico su macOS, Linux e Windows (nessun bash/launchd).
Avvialo all'accensione tramite il meccanismo del tuo OS (vedi
README_PORTABILITA.md). Resta in esecuzione e dorme tra un giro e l'altro;
Ollama viene avviato solo quando ci sono file e fermato a fine batch."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config
from ocrsys.runner import run_once


def main():
    while True:
        try:
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

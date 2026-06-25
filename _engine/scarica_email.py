"""Scarica subito in inbox gli allegati PDF delle email etichettate.
Utile per provare la configurazione: ocr-scarica-email

Il daemon fa la stessa cosa in automatico a ogni giro; questo comando serve a
verificare le credenziali ora, senza aspettare il prossimo ciclo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, email_fetch


def main():
    if not config.EMAIL_CONFIG.exists():
        print(f"Manca {config.EMAIL_CONFIG.name}. Copia "
              f"'.email.yaml.esempio' in '.email.yaml' e compila.")
        return
    n = email_fetch.scarica(stampa=True)
    print(f"\nScaricati {n} PDF in inbox.")


if __name__ == "__main__":
    main()

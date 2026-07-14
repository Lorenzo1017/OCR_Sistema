"""Rileva se un'app di scansione e' aperta: in tal caso il daemon NON processa
la inbox (evita di prendere PDF scritti a meta' durante la scansione). Riprende
da solo al giro successivo, quando l'app e' stata chiusa.

App da rilevare: impostazioni.yaml -> pausa_se_app_attiva: [Image Capture, ...].
Il confronto e' sul comando/percorso del processo (case-insensitive), cosi'
funziona col nome dell'eseguibile anche se il menu mostra il nome localizzato
(es. 'Acquisizione Immagine' = eseguibile 'Image Capture')."""
import subprocess
import sys

from . import config

_WIN = sys.platform.startswith("win")


def _processo_attivo(nome: str) -> bool:
    try:
        if _WIN:
            out = subprocess.run(["tasklist"], capture_output=True, text=True,
                                 timeout=5).stdout.lower()
            return nome.lower() in out
        if sys.platform == "darwin":
            # SOLO l'app GUI vera: il suo eseguibile sta in <Nome>.app/Contents/
            # MacOS/. Evita i demoni di sistema sempre attivi (es. 'icdd' per
            # Image Capture) che altrimenti terrebbero il daemon in pausa a vita.
            pat = f"{nome}.app/Contents/MacOS"
            r = subprocess.run(["pgrep", "-f", pat], capture_output=True, timeout=5)
            return r.returncode == 0
        # Linux: match sul comando completo, case-insensitive
        r = subprocess.run(["pgrep", "-f", "-i", nome],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False   # in dubbio, non bloccare la pipeline


def app_scanner_attiva():
    """Ritorna il nome della prima app scanner attiva, o None se nessuna."""
    for nome in (config.PAUSA_APP or []):
        if nome and _processo_attivo(nome):
            return nome
    return None

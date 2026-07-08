"""Controllo di salute proattivo: avvisa (notifica nativa) quando qualcosa
merita attenzione — la quarantena cresce o si accumulano documenti non smistati.
Stato salvato tra un giro e l'altro per notificare solo sui NUOVI casi, non a
ogni ciclo. Chiamato dal daemon dopo ogni passata."""
import json

from . import config
from .notify import notify

_STATO = config.SISTEMA / ".salute.json"
_SOGLIA_DASMISTARE = 25   # oltre questi non smistati, un promemoria


def _conta_pdf(cartella, ricorsivo=False):
    if not cartella.exists():
        return 0
    it = cartella.rglob("*") if ricorsivo else cartella.glob("*")
    return sum(1 for p in it if p.is_file()
               and p.suffix.lower() in config.INPUT_EXTS)


def _leggi():
    try:
        return json.loads(_STATO.read_text())
    except Exception:
        return {}


def _scrivi(d):
    try:
        _STATO.write_text(json.dumps(d))
    except OSError:
        pass


def controlla(notifiche: bool = True) -> dict:
    """Confronta lo stato attuale col precedente e notifica i peggioramenti.
    Ritorna il dict di stato corrente (quarantena, da_smistare)."""
    quar = _conta_pdf(config.DA_SMISTARE_ERRORI)
    dasm = _conta_pdf(config.DA_SMISTARE)      # solo il livello alto, non _errori
    prec = _leggi()
    if notifiche:
        # quarantena AUMENTATA: nuovi documenti irrecuperabili da guardare
        if quar > prec.get("quarantena", 0):
            nuovi = quar - prec.get("quarantena", 0)
            notify("OCR Sistema — attenzione",
                   f"{nuovi} nuovo/i documento/i in quarantena "
                   f"(_DaSmistare/_errori): totale {quar}.")
        # troppi non smistati: promemoria (solo al superamento della soglia)
        if dasm >= _SOGLIA_DASMISTARE > prec.get("da_smistare", 0):
            notify("OCR Sistema — da rivedere",
                   f"{dasm} documenti non smistati in _DaSmistare. "
                   f"Aprili in http://localhost:8077/revisiona")
    stato = {"quarantena": quar, "da_smistare": dasm}
    _scrivi(stato)
    return stato

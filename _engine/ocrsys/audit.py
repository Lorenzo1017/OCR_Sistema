"""Registro di audit append-only: traccia le operazioni che MODIFICANO
l'archivio (spostamenti, modifiche, eliminazioni, quarantena) con timestamp.
Serve a ricostruire 'cosa e' successo a questo documento' — requisito base di un
sistema di grado enterprise. Best-effort: un errore di scrittura non blocca mai
l'operazione vera."""
from datetime import datetime

from . import config


def registra(operazione: str, dettaglio: str = "") -> None:
    """Aggiunge una riga TSV: <ISO-timestamp>\\t<operazione>\\t<dettaglio>."""
    try:
        ts = datetime.now().isoformat(timespec="seconds")
        det = (dettaglio or "").replace("\t", " ").replace("\n", " ")
        with open(config.AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(f"{ts}\t{operazione}\t{det}\n")
    except OSError:
        pass

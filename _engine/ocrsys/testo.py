"""Pulizia del testo OCR PRIMA di mandarlo al LLM: toglie il boilerplate
ripetuto (intestazioni/pie' di pagina/disclaimer che si ripetono a ogni pagina)
e le righe rimosse via regex configurabili. Migliora la classificazione (meno
rumore) e accorcia il prompt. NB: il testo COMPLETO resta comunque salvato nel
DB per la ricerca; questa versione ripulita serve solo alla classificazione.

Regex utente in impostazioni.yaml -> rimuovi_dal_testo: ["...", "..."].
"""
import re

from . import config

# Righe di puro rumore quasi sempre inutili alla classificazione.
_RUMORE = re.compile(
    r"^\s*(pag(?:\.|ina)?\s*\d+(\s*/\s*\d+)?|\d+\s*/\s*\d+|[-_=.*·•]{3,})\s*$",
    re.IGNORECASE)


def _regex_utente():
    pats = []
    for p in (config.RIMUOVI_REGEX or []):
        try:
            pats.append(re.compile(p, re.IGNORECASE | re.MULTILINE))
        except re.error:
            pass
    return pats


def pulisci(testo: str) -> str:
    """Ritorna il testo ripulito. Se dopo la pulizia resta troppo poco
    (documento tutto 'boilerplate'), ritorna l'originale per non peggiorare."""
    if not testo:
        return testo
    originale = testo
    for rgx in _regex_utente():
        testo = rgx.sub("", testo)
    # deduplica le righe ripetute (header/footer uguali su piu' pagine),
    # scarta numeri di pagina/separatori, comprime i vuoti multipli.
    viste = {}
    out = []
    vuote = 0
    for riga in testo.splitlines():
        s = riga.strip()
        if not s:
            vuote += 1
            if vuote <= 1:
                out.append("")
            continue
        vuote = 0
        if _RUMORE.match(s):
            continue
        chiave = s.lower()
        viste[chiave] = viste.get(chiave, 0) + 1
        # una riga identica gia' vista 2+ volte = header/footer ripetuto: salta
        if viste[chiave] > 2:
            continue
        out.append(riga)
    pulito = "\n".join(out).strip()
    return pulito if len(pulito) >= 30 else originale
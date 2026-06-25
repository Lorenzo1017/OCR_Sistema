"""Scarica in inbox gli allegati PDF delle email Gmail con una certa etichetta,
da quando la funzione e' stata attivata in poi. Gira headless (lo chiama il
daemon a ogni giro). Non modifica la casella: la deduplica e' su Message-ID
salvati in uno stato locale.

Configurazione: _Sistema/.email.yaml (gitignorato, chmod 600):
    attivo: true
    email: tuoindirizzo@gmail.com
    app_password: "xxxx xxxx xxxx xxxx"   # password per app Google (2FA)
    etichetta: Add_OCR                     # etichetta Gmail da monitorare
    imap_host: imap.gmail.com              # opzionale
"""
import email
import imaplib
import json
import re
from datetime import date
from email.header import decode_header
from pathlib import Path

import yaml

from . import config

_MESI = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _leggi_config() -> dict:
    p = config.EMAIL_CONFIG
    if not p.exists():
        return {}
    try:
        data = yaml.safe_load(p.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _leggi_stato() -> dict:
    p = config.EMAIL_STATE
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def _scrivi_stato(stato: dict):
    config.EMAIL_STATE.write_text(json.dumps(stato))


def _data_imap(d: date) -> str:
    """date -> 'GG-Mon-AAAA' per il comando SEARCH SINCE di IMAP."""
    return f"{d.day:02d}-{_MESI[d.month - 1]}-{d.year}"


def _decodifica(s: str) -> str:
    """Decodifica un header MIME (=?utf-8?...?=) in stringa leggibile."""
    out = []
    for testo, enc in decode_header(s or ""):
        if isinstance(testo, bytes):
            out.append(testo.decode(enc or "utf-8", "ignore"))
        else:
            out.append(testo)
    return "".join(out)


def _nome_sicuro(nome: str) -> str:
    """Ripulisce il nome dell'allegato (niente separatori di percorso)."""
    nome = _decodifica(nome).strip()
    nome = re.sub(r"[/\\\x00]", "_", nome)
    return nome or "allegato.pdf"


def _nome_libero(dest_dir: Path, nome: str) -> Path:
    p = dest_dir / nome
    if not p.exists():
        return p
    stem, suf = (nome[:-4], nome[-4:]) if nome.lower().endswith(".pdf") else (nome, "")
    i = 2
    while (dest_dir / f"{stem}_{i}{suf}").exists():
        i += 1
    return dest_dir / f"{stem}_{i}{suf}"


def _pdf_allegati(msg) -> list:
    """Ritorna [(nome, bytes)] dei soli allegati PDF del messaggio."""
    out = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        nome = part.get_filename()
        ctype = (part.get_content_type() or "").lower()
        if not nome:
            continue
        if ctype == "application/pdf" or _decodifica(nome).lower().endswith(".pdf"):
            payload = part.get_payload(decode=True)
            if payload:
                out.append((_nome_sicuro(nome), payload))
    return out


def scarica(stampa: bool = False) -> int:
    """Scarica i PDF delle email etichettate (da data attivazione in poi) in
    inbox. Ritorna quanti file salvati. Silenzioso/robusto: se non configurato
    o se la rete e' giu', ritorna 0 senza sollevare (il daemon non deve morire)."""
    cfg = _leggi_config()
    if not cfg.get("attivo") or not cfg.get("email") or not cfg.get("app_password"):
        return 0
    etichetta = str(cfg.get("etichetta", "Add_OCR"))
    host = str(cfg.get("imap_host", "imap.gmail.com"))

    stato = _leggi_stato()
    # "da oggi in poi": fissa la data di attivazione al primo giro e usala come
    # limite inferiore della SEARCH (lo storico precedente viene ignorato).
    dal = stato.get("dal")
    if not dal:
        dal = date.today().isoformat()
        stato["dal"] = dal
        _scrivi_stato(stato)
    y, m, d = (int(x) for x in dal.split("-"))
    since = _data_imap(date(y, m, d))
    visti = set(stato.get("visti", []))

    config.ensure_dirs()
    salvati = 0
    imap = None
    try:
        imap = imaplib.IMAP4_SSL(host)
        imap.login(cfg["email"], cfg["app_password"])
        # le etichette Gmail sono "mailbox" IMAP: selezionala in sola lettura
        typ, _ = imap.select(f'"{etichetta}"', readonly=True)
        if typ != "OK":
            if stampa:
                print(f"Etichetta '{etichetta}' non trovata su Gmail.")
            return 0
        typ, dati = imap.search(None, "SINCE", since)
        if typ != "OK":
            return 0
        for num in dati[0].split():
            typ, raw = imap.fetch(num, "(RFC822)")
            if typ != "OK" or not raw or not raw[0]:
                continue
            msg = email.message_from_bytes(raw[0][1])
            mid = (msg.get("Message-ID") or "").strip()
            if mid and mid in visti:
                continue
            for nome, payload in _pdf_allegati(msg):
                dest = _nome_libero(config.INBOX, nome)
                dest.write_bytes(payload)
                salvati += 1
                if stampa:
                    print(f"email -> inbox/{dest.name}")
            if mid:
                visti.add(mid)
        stato["visti"] = sorted(visti)
        _scrivi_stato(stato)
    except Exception as e:
        if stampa:
            print(f"Fetch email saltato: {str(e)[:80]}")
        return salvati
    finally:
        if imap is not None:
            try:
                imap.logout()
            except Exception:
                pass
    return salvati

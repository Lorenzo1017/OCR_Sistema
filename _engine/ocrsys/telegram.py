"""Logica (testabile) del bot Telegram: config, autorizzazione, parsing comandi
e composizione delle risposte. La parte di rete (polling + chiamate API) sta in
telegram_bot.py.

Sicurezza: il bot risponde SOLO alle chat autorizzate (chat_id in .telegram.yaml).
Chi non e' in lista riceve il proprio id e nessun dato -> l'archivio non e'
esposto a chiunque trovi il bot.
"""
import yaml

from . import config

MAX_RISULTATI = 8      # righe mostrate nella risposta testuale
MAX_PDF = 3            # quanti PDF allegare per ricerca (evita spam)


def leggi_config() -> dict:
    p = config.SISTEMA / ".telegram.yaml"
    try:
        if p.exists():
            d = yaml.safe_load(p.read_text())
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


def chat_autorizzate(cfg: dict) -> set:
    raw = cfg.get("chat_id", [])
    if not isinstance(raw, list):
        raw = [raw]
    return {str(x) for x in raw if str(x).strip()}


def autorizzato(chat_id, cfg: dict) -> bool:
    ammesse = chat_autorizzate(cfg)
    return bool(ammesse) and str(chat_id) in ammesse


def comando(testo: str) -> tuple:
    """'/cerca mutuo 2024' -> ('cerca', 'mutuo 2024'). Gestisce anche il suffisso
    del bot '/cerca@MioBot'. Ritorna ('', '') se non e' un comando."""
    testo = (testo or "").strip()
    if not testo.startswith("/"):
        return "", ""
    parti = testo[1:].split(maxsplit=1)
    cmd = parti[0].split("@")[0].lower()
    arg = parti[1].strip() if len(parti) > 1 else ""
    return cmd, arg


_AIUTO = ("📁 *Archivio OCR*\n"
          "/cerca <parole> — cerca nei documenti e ricevi i PDF\n"
          "/stato — quanti documenti, categorie, da rivedere\n"
          "/aiuto — questo messaggio")


def risposta(db, testo: str) -> tuple:
    """Interpreta il messaggio e ritorna (testo_markdown, [percorsi_pdf]).
    Percorsi relativi a config.BASE, da inviare come documenti."""
    cmd, arg = comando(testo)
    if cmd in ("start", "aiuto", "help"):
        return _AIUTO, []
    if cmd == "stato":
        return _stato(db), []
    if cmd == "cerca":
        if not arg:
            return "Scrivi cosa cercare, es: `/cerca mutuo 2024`", []
        return _cerca(db, arg)
    return ("Comando non riconosciuto. Usa /cerca, /stato o /aiuto.", [])


def _stato(db) -> str:
    c = db.conn
    tot = c.execute("SELECT COUNT(*) FROM documenti").fetchone()[0]
    ncat = c.execute("SELECT COUNT(DISTINCT categoria) FROM documenti").fetchone()[0]
    rivedi = c.execute("SELECT COUNT(*) FROM documenti WHERE confidenza='bassa' "
                       "OR percorso LIKE '\\_DaSmistare%' ESCAPE '\\'").fetchone()[0]
    return (f"📊 *Archivio*\n{tot} documenti · {ncat} categorie\n"
            f"{rivedi} da rivedere")


def _cerca(db, query: str) -> tuple:
    ris = db.search(query)
    if not ris:
        return (f"Nessun documento per «{query}».", [])
    righe = [f"🔎 {len(ris)} risultati per «{query}»:"]
    for r in ris[:MAX_RISULTATI]:
        righe.append(f"• {r['data_documento']} — {r['categoria']}\n  {r['nome_file']}")
    if len(ris) > MAX_RISULTATI:
        righe.append(f"…e altri {len(ris) - MAX_RISULTATI}. Invio i primi {MAX_PDF} PDF.")
    pdf = [r["percorso"] for r in ris[:MAX_PDF]]
    return "\n".join(righe), pdf

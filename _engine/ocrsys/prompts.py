"""Prompt LLM editabili dall'utente. Al primo uso il default viene scritto in
_Sistema/prompts/<nome>; da quel momento l'utente puo' ritoccarlo senza toccare
il codice. Se il file esiste si usa quello, altrimenti il default (robusto: se
il file e' illeggibile si torna al default).

I segnaposto si riempiono per SOSTITUZIONE ({categorie}, {mittenti}, {testo}):
cosi' eventuali graffe delle graffe JSON negli esempi non rompono nulla (a
differenza di str.format)."""
from . import config


def carica(nome: str, default: str) -> str:
    """Ritorna il testo del prompt: dal file se presente, altrimenti scrive il
    default (materializzandolo per l'editing) e lo ritorna."""
    path = config.PROMPTS_DIR / nome
    try:
        if path.exists():
            testo = path.read_text(encoding="utf-8").strip()
            if testo:
                return testo
        # prima volta: materializza il default cosi' l'utente lo trova da editare
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default, encoding="utf-8")
    except OSError:
        pass
    return default


def riempi(template: str, **segnaposti) -> str:
    """Sostituisce {chiave} con il valore, senza toccare altre graffe."""
    for k, v in segnaposti.items():
        template = template.replace("{" + k + "}", str(v))
    return template

import shutil

from . import config


def check(require_ollama: bool = True) -> list:
    """Verifica che l'ambiente sia pronto. Ritorna lista di problemi (stringhe);
    lista vuota = tutto ok. Evita che ogni file finisca in errore per una
    dipendenza mancante."""
    problemi = []

    for tool in ("tesseract", "ocrmypdf"):
        if not shutil.which(tool):
            problemi.append(
                f"Manca '{tool}'. Installalo (vedi README_PORTABILITA.md)."
            )

    if not config.CATEGORIE_YAML.exists():
        problemi.append(f"Manca il file categorie: {config.CATEGORIE_YAML}")

    if require_ollama and not shutil.which("ollama"):
        problemi.append(
            "Manca 'ollama'. Installalo da https://ollama.com (serve per "
            "classificare i documenti)."
        )

    return problemi

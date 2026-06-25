"""OCR Vision: per i documenti che Tesseract NON riesce a leggere (scansioni
immagine, libri), si rendono le prime pagine in immagine e si chiede a un
modello vision locale (qwen2.5vl) di leggerle e classificarle.
NB: non deve mai girare insieme al modello text -> il chiamante scarica l'altro
modello e usa il lock unico."""
import base64
import json
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from . import config
from .classify import parse_response

_PROMPT = """Sei un archivista. Guarda l'immagine del documento, LEGGILA e classificala.
Rispondi SOLO con un oggetto JSON, niente altro.

Categorie ammesse (scegli ESATTAMENTE una di queste stringhe):
{categorie}
{mittenti}
Schema:
{{"data":"AAAA-MM-GG","mittente":"...","tipo":"...","dettaglio":"...","categoria":"<una delle ammesse>","tags":["..."],"confidenza":"alta|media|bassa","testo":"trascrizione del testo principale"}}

Regole: "mittente"=chi emette; categoria DEVE essere una delle ammesse, se nessuna
calza usa ""; "testo"=trascrivi il contenuto leggibile (per la ricerca).
JSON:"""


def disponibile() -> bool:
    return shutil.which("pdftoppm") is not None


def _render(pdf: Path, out_dir: Path, pagine: int = 2, lato_max: int = 2000) -> list:
    # -scale-to limita il lato lungo a `lato_max` px: scansioni ad alta
    # risoluzione producono PNG da diversi MB che Ollama rifiuta (HTTP 400).
    # Cosi' l'immagine resta leggibile ma il payload contenuto.
    subprocess.run(
        ["pdftoppm", "-png", "-f", "1", "-l", str(pagine),
         "-scale-to", str(lato_max), str(pdf), str(out_dir / "pag")],
        check=True, capture_output=True,
    )
    return sorted(out_dir.glob("pag*.png"))


def _call(prompt: str, imgs_b64: list) -> str:
    payload = json.dumps({
        "model": config.OLLAMA_VISION_MODEL, "prompt": prompt,
        "images": imgs_b64, "stream": False, "format": "json",
        "keep_alive": config.OLLAMA_KEEP_ALIVE,
        # num_ctx alto: 2 immagini + prompt sforano il default 4096 -> il JSON
        # di risposta verrebbe troncato a meta' (output invalido). 8192 lascia
        # spazio sia alle immagini sia alla risposta completa.
        "options": {"temperature": 0, "num_ctx": 8192},
    }).encode()
    req = urllib.request.Request(
        config.OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read()).get("response", "")


def classifica(pdf: Path, taxonomy, mittenti_noti=None) -> dict:
    """Classifica un PDF leggendone le immagini. Ritorna il dict meta (come
    classify.parse_response) con in piu' 'testo' (trascrizione per l'indice)."""
    with tempfile.TemporaryDirectory() as td:
        imgs = _render(pdf, Path(td))
        if not imgs:
            return {"valido": False, "testo": ""}
        b64 = [base64.b64encode(p.read_bytes()).decode() for p in imgs[:2]]
        # NB: NON iniettiamo la lista mittenti noti (a differenza del modello
        # text): col vision legge il mittente direttamente dall'immagine, e la
        # lista gonfierebbe il context riducendo lo spazio per la risposta.
        prompt = _PROMPT.format(
            categorie="\n".join(sorted(taxonomy.valid_paths())), mittenti="")
        raw = _call(prompt, b64)
    r = parse_response(raw, taxonomy)
    try:
        data = json.loads(raw)
        r["testo"] = str(data.get("testo", "")) if isinstance(data, dict) else ""
    except Exception:
        r["testo"] = ""
    return r

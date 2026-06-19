import json
import re
import urllib.request
from .config import OLLAMA_MODEL, OLLAMA_URL
from .taxonomy import Taxonomy

_REQUIRED = {"data", "mittente", "tipo", "dettaglio", "categoria", "confidenza"}

_PROMPT = """Sei un archivista. Leggi il testo OCR di un documento e rispondi
SOLO con un oggetto JSON, senza altro testo.

Categorie ammesse (scegli ESATTAMENTE una di queste stringhe, niente altro):
{categorie}

Schema richiesto:
{{"data":"AAAA-MM-GG","mittente":"...","tipo":"...","dettaglio":"...","categoria":"<una delle ammesse>","confidenza":"alta|media|bassa"}}

Regole:
- "data" = data di emissione del documento. Se non sicura, usa "".
- "mittente" = chi emette (es. Enel, Agenzia Entrate). Breve.
- "tipo" = natura (bolletta, fattura, referto, contratto...).
- "dettaglio" = specifica breve (gas, IMU, auto...) o "".
- "categoria" DEVE essere una delle ammesse. Se nessuna calza, usa "".
- "confidenza" = quanto sei sicuro della categoria.

Testo OCR (primi caratteri):
---
{testo}
---
JSON:"""


def _extract_json(raw: str):
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def parse_response(raw: str, taxonomy: Taxonomy) -> dict:
    data = _extract_json(raw)
    if not isinstance(data, dict) or not _REQUIRED.issubset(data.keys()):
        return {"valido": False}
    cat = data.get("categoria", "")
    conf = data.get("confidenza", "")
    valido = taxonomy.is_valid(cat) and conf in ("alta", "media")
    return {
        "data": data.get("data") or None,
        "mittente": data.get("mittente", ""),
        "tipo": data.get("tipo", ""),
        "dettaglio": data.get("dettaglio", ""),
        "categoria": cat,
        "confidenza": conf,
        "valido": bool(valido),
    }


def _call_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL, "prompt": prompt,
        "stream": False, "format": "json",
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
    return body.get("response", "")


def classify(text: str, taxonomy: Taxonomy) -> dict:
    categorie = "\n".join(sorted(taxonomy.valid_paths()))
    prompt = _PROMPT.format(categorie=categorie, testo=text[:4000])
    raw = _call_ollama(prompt)
    return parse_response(raw, taxonomy)

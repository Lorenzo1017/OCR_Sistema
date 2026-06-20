import json
import re
import urllib.request
from .config import OLLAMA_MODEL, OLLAMA_URL, OLLAMA_KEEP_ALIVE
from .taxonomy import Taxonomy

_REQUIRED = {"data", "mittente", "tipo", "dettaglio", "categoria", "confidenza"}

_PROMPT = """Sei un archivista esperto. Leggi il testo OCR di un documento e
classificalo. Rispondi SOLO con un oggetto JSON, senza altro testo.

Categorie ammesse (scegli ESATTAMENTE una di queste stringhe, niente altro):
{categorie}

Schema richiesto:
{{"data":"AAAA-MM-GG","mittente":"...","tipo":"...","dettaglio":"...","categoria":"<una delle ammesse>","confidenza":"alta|media|bassa"}}

Regole:
- Ragiona prima sul MITTENTE e sul TIPO di documento, poi scegli la categoria piu' coerente.
- "data" = data di emissione del documento (formato AAAA-MM-GG). Se non sicura, usa "".
- "mittente" = chi emette (es. Enel, Agenzia delle Entrate, Vodafone). Breve.
- "tipo" = natura (bolletta, fattura, referto, contratto, cartella, busta paga...).
- "dettaglio" = specifica breve (gas, internet, IMU, auto...) o "".
- "categoria" DEVE essere una delle ammesse sopra. Se nessuna calza, usa "".
- "confidenza" = quanto sei sicuro della categoria (alta/media/bassa).

Esempi (mittente -> categoria):
- Enel/Eni/A2A bolletta luce o gas -> Casa/Utenze/Luce o Casa/Utenze/Gas
- Vodafone/TIM/WindTre/Iliad fattura telefono o internet -> Casa/Utenze/Internet o Casa/Utenze/Telefono
- Agenzia delle Entrate, cartella o IMU/TARI -> Fisco-Tasse/IMU-TARI
- Ospedale/ASL/laboratorio analisi, referto -> Salute/Referti
- Banca (Intesa, Unicredit...), estratto conto -> Banca-Finanze/EstrattiConto
- Datore di lavoro, busta paga/cedolino -> Lavoro/BustePaga

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
    cat = str(data.get("categoria", "")).strip().strip("/")
    conf = str(data.get("confidenza", "")).strip().lower()
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


# Pattern per disambiguare i sotto-tipi di utenza (errore comune del 7B: bolletta
# acqua filata sotto Luce per una riga di boilerplate). Confini di parola per
# evitare falsi positivi ("gas" dentro "gasolio", "sim" dentro "simile",
# "mobile" dentro "automobile"). I `\w*` coprono le desinenze (elettric-a/-o).
_UTENZE_RE = {
    "Gas": r"\bgas\b|\bsmc\b|\bmetano\b",
    "Luce": r"\benergia elettrica\b|\bkwh\b|\bkilowatt\w*|\belettric\w*",
    "Acqua": r"\bacqua\w*|\bacque\w*|\bidric\w*|\bacquedott\w*|\bfognatur\w*|\bdepurazion\w*",
    "Internet": r"\binternet\b|\bfibra\b|\badsl\b|\bgiga\b|\bbanda larga\b",
    "Telefono": r"\btelefon\w*|\bmobile\b|\bsim\b|\bricaric\w*|\bcellular\w*",
}
_UTENZE_KW = _UTENZE_RE   # alias per compatibilita' (chi controlla i leaf)
_UTENZE_COMPILED = {leaf: re.compile(pat) for leaf, pat in _UTENZE_RE.items()}


def _punteggi(text: str) -> dict:
    t = text.lower()
    return {leaf: len(rx.findall(t)) for leaf, rx in _UTENZE_COMPILED.items()}


def valuta_utenza(categoria: str, text: str):
    """Per categorie Casa/Utenze/*: confronta la scelta del modello col testo.
    Ritorna (categoria_finale, valido).
    - dominante chiaro diverso dalla scelta -> auto-correzione;
    - mismatch non dominante -> valido=False (-> _DaSmistare);
    - scelta coerente o nessun segnale -> invariato."""
    leaf = categoria.split("/")[-1]
    if leaf not in _UTENZE_KW:
        return categoria, True
    sc = _punteggi(text)
    best = max(sc, key=sc.get)
    best_s = sc[best]
    if best_s == 0:
        return categoria, True            # nessun segnale: fiducia al modello
    if best == leaf:
        return categoria, True            # scelta coerente
    # un'altra utenza ha piu' riscontri della scelta
    if best_s >= 3 and best_s >= 3 * sc.get(leaf, 0):
        return f"Casa/Utenze/{best}", True   # dominanza netta -> correggi
    return categoria, False               # mismatch ambiguo -> _DaSmistare


def _call_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL, "prompt": prompt,
        "stream": False, "format": "json",
        "keep_alive": OLLAMA_KEEP_ALIVE,   # modello si scarica dopo l'uso
        "options": {"temperature": 0},
    }).encode()
    # 1 retry su blip transitori (server che ha appena caricato il modello)
    last = None
    for tentativo in range(2):
        try:
            req = urllib.request.Request(
                OLLAMA_URL, data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read())
            return body.get("response", "")
        except OSError as e:   # URLError e socket.timeout sono sottoclassi
            last = e
    raise last


def classify(text: str, taxonomy: Taxonomy) -> dict:
    categorie = "\n".join(sorted(taxonomy.valid_paths()))
    prompt = _PROMPT.format(categorie=categorie, testo=text[:4000])
    raw = _call_ollama(prompt)
    r = parse_response(raw, taxonomy)
    # guardia utenze: usa testo OCR + dettaglio/tipo del modello come evidenza.
    if r.get("valido") and r["categoria"].startswith("Casa/Utenze/"):
        evidenza = f"{r.get('dettaglio','')} {r.get('tipo','')} {text}"
        nuova, ok = valuta_utenza(r["categoria"], evidenza)
        if not ok:
            r["valido"] = False
        else:
            r["categoria"] = nuova
    return r

import datetime
import re

_MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5,
    "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9,
    "ottobre": 10, "novembre": 11, "dicembre": 12,
}

_NUM = re.compile(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b")
_TESTO = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(_MESI) + r")\s+(\d{4})\b", re.IGNORECASE
)


def _norm_year(y: int) -> int:
    if y >= 100:
        return y
    # pivot: 00-50 -> 20xx, 51-99 -> 19xx (un '98' e' il 1998, non il 2098)
    return 2000 + y if y <= 50 else 1900 + y


def _anno_max() -> int:
    # un documento non puo' essere del futuro (tolleranza 1 anno per post-datati)
    return datetime.date.today().year + 1


def _valid(g: int, m: int, a: int) -> bool:
    # plausibilita': giorno/mese validi e anno tra 1970 e l'anno prossimo
    # (scarta allucinazioni tipo 2079 o anni assurdi dall'OCR).
    return 1 <= g <= 31 and 1 <= m <= 12 and 1970 <= a <= _anno_max()


_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def normalize_date(s):
    """Normalizza una stringa data in 'AAAA-MM-GG'. Accetta gia' ISO o formati
    italiani (15/03/2024, 15.03.24, 15 marzo 2024). Ritorna None se non valida."""
    if not s:
        return None
    s = s.strip()
    m = _ISO.match(s)
    if m:
        a, mo, g = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{a:04d}-{mo:02d}-{g:02d}" if _valid(g, mo, a) else None
    return extract_date(s)


def extract_date(text: str):
    candidates = []
    for m in _NUM.finditer(text):
        g, mo, a = int(m.group(1)), int(m.group(2)), _norm_year(int(m.group(3)))
        # recupero gg/mm vs mm/gg: se il "mese" e' >12 ma il "giorno" e' <=12,
        # probabilmente era in ordine americano -> scambia.
        if mo > 12 and g <= 12:
            g, mo = mo, g
        if _valid(g, mo, a):
            candidates.append((m.start(), a, mo, g))
    for m in _TESTO.finditer(text):
        g = int(m.group(1))
        mo = _MESI[m.group(2).lower()]
        a = int(m.group(3))
        if _valid(g, mo, a):
            candidates.append((m.start(), a, mo, g))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    _, a, mo, g = candidates[0]
    return f"{a:04d}-{mo:02d}-{g:02d}"

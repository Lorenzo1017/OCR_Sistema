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
    return 2000 + y if y < 100 else y


def _valid(g: int, m: int, a: int) -> bool:
    return 1 <= g <= 31 and 1 <= m <= 12 and 1900 <= a <= 2100


def extract_date(text: str):
    candidates = []
    for m in _NUM.finditer(text):
        g, mo, a = int(m.group(1)), int(m.group(2)), _norm_year(int(m.group(3)))
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

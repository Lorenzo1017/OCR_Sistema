import re
from pathlib import Path


def _slug(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"[/\\]", "", s)
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s.strip("-")


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def build_name(data, mittente, tipo, dettaglio) -> str:
    # difesa: accetta solo data gia' in formato AAAA-MM-GG, mai slash nel nome
    d = data if (data and _ISO_DATE.match(data)) else "0000-00-00"
    parts = [_slug(mittente) or "Ignoto", _slug(tipo) or "documento"]
    det = _slug(dettaglio)
    if det:
        parts.append(det)
    return f"{d}_{'_'.join(parts)}.pdf"


def resolve_collision(folder: Path, name: str) -> str:
    target = folder / name
    if not target.exists():
        return name
    stem = name[:-4]
    i = 2
    while (folder / f"{stem}_v{i}.pdf").exists():
        i += 1
    return f"{stem}_v{i}.pdf"

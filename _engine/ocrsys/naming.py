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


# Tetto alla lunghezza del nome file. Il limite del filesystem e' 255 byte per
# componente (macOS/ext4): col vision il "dettaglio" puo' essere una frase intera
# e sforare -> "File name too long". 180 lascia margine per il suffisso _vN.
_MAX_NAME = 180


def build_name(data, mittente, tipo, dettaglio) -> str:
    # difesa: accetta solo data gia' in formato AAAA-MM-GG, mai slash nel nome
    d = data if (data and _ISO_DATE.match(data)) else "0000-00-00"
    parts = [_slug(mittente) or "Ignoto", _slug(tipo) or "documento"]
    det = _slug(dettaglio)
    if det:
        parts.append(det)
    name = f"{d}_{'_'.join(parts)}.pdf"
    if len(name.encode("utf-8")) > _MAX_NAME:
        # taglia solo la coda (il dettaglio), preservando data_mittente_tipo
        base = f"{d}_{_slug(mittente) or 'Ignoto'}_{_slug(tipo) or 'documento'}"
        avail = _MAX_NAME - len(base.encode("utf-8")) - len("_.pdf")
        coda = det.encode("utf-8")[:max(0, avail)].decode("utf-8", "ignore")
        name = f"{base}_{coda}.pdf" if coda else f"{base}.pdf"
    return name


def resolve_collision(folder: Path, name: str) -> str:
    target = folder / name
    if not target.exists():
        return name
    stem = name[:-4]
    i = 2
    while (folder / f"{stem}_v{i}.pdf").exists():
        i += 1
    return f"{stem}_v{i}.pdf"

import subprocess
from pathlib import Path
from pypdf import PdfReader
from .config import OCR_MIN_TEXT

# Flag comuni: lingua italiana, raddrizza scansioni storte, ruota pagine
# capovolte. Migliora l'OCR su scansioni reali disordinate.
_COMMON = ["-l", "ita", "--deskew", "--rotate-pages", "--image-dpi", "300"]


def _run(src: Path, out_pdf: Path, mode: str) -> None:
    subprocess.run(
        ["ocrmypdf", *_COMMON, mode, str(src), str(out_pdf)],
        check=True, capture_output=True,
    )


def _quick_text(pdf: Path) -> str:
    try:
        reader = PdfReader(str(pdf))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""


def ocr_to_pdf(src: Path, out_pdf: Path) -> None:
    """OCR di src -> PDF cercabile in out_pdf. src puo' essere PDF o immagine.

    Strategia robusta (F5):
    - prima passa con --skip-text (OCR solo pagine senza testo): veloce, ideale
      per scansioni immagine pure;
    - se il testo risulta troppo scarso (PDF con layer di testo sporco gia'
      presente, saltato da --skip-text) o se ocrmypdf fallisce, ritenta con
      --force-ocr che ri-OCR tutto da zero.
    """
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run(src, out_pdf, "--skip-text")
        if len(_quick_text(out_pdf).strip()) >= OCR_MIN_TEXT:
            return
    except subprocess.CalledProcessError:
        pass
    # fallback: ri-OCR completo
    _run(src, out_pdf, "--force-ocr")


def extract_text(pdf: Path):
    """Ritorna (testo, n_pagine) dal PDF cercabile."""
    reader = PdfReader(str(pdf))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages), len(reader.pages)

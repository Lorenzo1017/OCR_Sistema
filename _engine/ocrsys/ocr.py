import subprocess
from pathlib import Path
from pypdf import PdfReader


def ocr_to_pdf(src: Path, out_pdf: Path) -> None:
    """OCR di src -> PDF cercabile in out_pdf. src puo essere PDF o immagine."""
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ocrmypdf", "-l", "ita", "--image-dpi", "300",
         "--skip-text", str(src), str(out_pdf)],
        check=True, capture_output=True,
    )


def extract_text(pdf: Path):
    """Ritorna (testo, n_pagine) dal PDF cercabile."""
    reader = PdfReader(str(pdf))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages), len(reader.pages)

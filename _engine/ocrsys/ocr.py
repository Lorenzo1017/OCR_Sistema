import shutil
import subprocess
from pathlib import Path
from pypdf import PdfReader
from . import config
from .config import OCR_MIN_TEXT, TESTO_NATIVO_MIN

# Flag comuni: lingua/e configurabile/i (impostazioni.yaml -> ocr_lingue),
# raddrizza scansioni storte, ruota pagine capovolte.
_COMMON = ["-l", config.OCR_LINGUE, "--deskew", "--rotate-pages",
           "--image-dpi", "300"]


def _run(src: Path, out_pdf: Path, mode: str) -> None:
    r = subprocess.run(
        ["ocrmypdf", *_COMMON, mode, str(src), str(out_pdf)],
        capture_output=True,
    )
    if r.returncode != 0:
        # include lo stderr di ocrmypdf nel messaggio (altrimenti il log dice
        # solo "exit status N" e il debug e' impossibile)
        err = (r.stderr or b"").decode("utf-8", "replace").strip()[-400:]
        raise subprocess.CalledProcessError(
            r.returncode, "ocrmypdf", output=r.stdout, stderr=err)


def _read_pdf_text(pdf: Path) -> tuple:
    # apre il file esplicitamente e lo chiude (su Windows un handle aperto puo'
    # impedire la cancellazione della cartella temporanea)
    with open(pdf, "rb") as fh:
        reader = PdfReader(fh)
        pages = [(p.extract_text() or "") for p in reader.pages]
        return "\n".join(pages), len(pages)


def _quick_text(pdf: Path) -> str:
    try:
        return _read_pdf_text(pdf)[0]
    except Exception:
        return ""


def ocr_to_pdf(src: Path, out_pdf: Path) -> None:
    """OCR di src -> PDF cercabile in out_pdf. src puo' essere PDF o immagine.

    Strategia robusta:
    - se il PDF ha gia' un buon layer di testo (firmato digitalmente, PEC,
      export nativo), lo si usa cosi' com'e': niente OCR (ocrmypdf rifiuta i
      firmati con DigitalSignatureError) e molto piu' veloce;
    - altrimenti --skip-text (OCR solo pagine senza testo), ideale per scansioni;
    - se il testo risulta troppo scarso o ocrmypdf fallisce, ritenta con
      --force-ocr che ri-OCR tutto da zero;
    - se anche il force-ocr fallisce ma un po' di testo nativo c'era, si usa
      quello (meglio che perdere il documento in quarantena).
    """
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    nativo = _quick_text(src).strip() if src.suffix.lower() == ".pdf" else ""
    if len(nativo) >= TESTO_NATIVO_MIN:
        shutil.copyfile(str(src), str(out_pdf))
        return
    try:
        _run(src, out_pdf, "--skip-text")
        if len(_quick_text(out_pdf).strip()) >= OCR_MIN_TEXT:
            return
    except subprocess.CalledProcessError:
        pass
    try:
        _run(src, out_pdf, "--force-ocr")
    except subprocess.CalledProcessError:
        if nativo:                      # firmato senza layer immagine OCR-abile
            shutil.copyfile(str(src), str(out_pdf))
        else:
            raise


def extract_text(pdf: Path):
    """Ritorna (testo, n_pagine) dal PDF cercabile."""
    return _read_pdf_text(pdf)

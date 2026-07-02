import subprocess

import pytest

from ocrsys import ocr


def test_pdf_con_testo_nativo_salta_ocr(tmp_path, monkeypatch):
    src = tmp_path / "firmato.pdf"
    src.write_bytes(b"%PDF fake")
    out = tmp_path / "out.pdf"
    monkeypatch.setattr(ocr, "_quick_text", lambda p: "x" * 200)  # testo nativo
    chiamato = {"run": False}
    monkeypatch.setattr(ocr, "_run",
                        lambda *a, **k: chiamato.__setitem__("run", True))
    ocr.ocr_to_pdf(src, out)
    assert out.exists()            # copiato
    assert chiamato["run"] is False  # ocrmypdf MAI chiamato


def test_scansione_senza_testo_fa_ocr(tmp_path, monkeypatch):
    src = tmp_path / "scan.pdf"
    src.write_bytes(b"%PDF fake")
    out = tmp_path / "out.pdf"
    monkeypatch.setattr(ocr, "_quick_text", lambda p: "")  # nessun testo nativo
    modi = []
    monkeypatch.setattr(ocr, "_run", lambda s, o, m: modi.append(m))
    # _quick_text sull'output resta "" -> non raggiunge OCR_MIN -> prova force
    ocr.ocr_to_pdf(src, out)
    assert modi == ["--skip-text", "--force-ocr"]


def test_firmato_senza_layer_ocr_usa_nativo(tmp_path, monkeypatch):
    # PDF firmato con poco testo (< soglia nativo) ma ocrmypdf fallisce sempre:
    # come ultima spiaggia usa il testo nativo invece di sollevare.
    src = tmp_path / "firmato2.pdf"
    src.write_bytes(b"%PDF fake")
    out = tmp_path / "out.pdf"
    monkeypatch.setattr(ocr, "_quick_text",
                        lambda p: "poco testo firmato")  # < TESTO_NATIVO_MIN
    def boom(*a, **k):
        raise subprocess.CalledProcessError(2, "ocrmypdf", stderr="DigitalSignatureError")
    monkeypatch.setattr(ocr, "_run", boom)
    ocr.ocr_to_pdf(src, out)       # non deve sollevare
    assert out.exists()


def test_scansione_pura_fallita_solleva(tmp_path, monkeypatch):
    # nessun testo nativo e ocrmypdf fallisce -> deve sollevare (quarantena)
    src = tmp_path / "rotto.pdf"
    src.write_bytes(b"%PDF fake")
    out = tmp_path / "out.pdf"
    monkeypatch.setattr(ocr, "_quick_text", lambda p: "")
    def boom(*a, **k):
        raise subprocess.CalledProcessError(2, "ocrmypdf", stderr="boom")
    monkeypatch.setattr(ocr, "_run", boom)
    with pytest.raises(subprocess.CalledProcessError):
        ocr.ocr_to_pdf(src, out)

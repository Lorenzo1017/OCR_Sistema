import shutil
from pathlib import Path
from ocrsys.pipeline import process_file, Context
from ocrsys.taxonomy import Taxonomy
from ocrsys.db import Database

def make_ctx(tmp_path, classify_result, text="Enel gas 15/03/2024"):
    base = tmp_path
    for d in ["inbox", "archivio", "originali", "text", "_DaSmistare"]:
        (base / d).mkdir()
    tax = Taxonomy({"Casa/Utenze/Gas"})
    db = Database(base / "index.db")

    def fake_ocr(src, out_pdf):
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        out_pdf.write_text("pdf")

    def fake_extract(pdf):
        return text, 1

    def fake_classify(t, taxonomy):
        return classify_result

    return Context(
        base=base, taxonomy=tax, db=db,
        ocr_to_pdf=fake_ocr, extract_text=fake_extract, classify=fake_classify,
    )

def test_valid_doc_routed_to_archivio(tmp_path):
    src = tmp_path / "scan.pdf"; src.write_text("x")
    ctx = make_ctx(tmp_path, {
        "valido": True, "data": "2024-03-15", "mittente": "Enel",
        "tipo": "bolletta", "dettaglio": "gas",
        "categoria": "Casa/Utenze/Gas", "confidenza": "alta",
    })
    process_file(src, ctx)
    out = tmp_path / "archivio/Casa/Utenze/Gas/2024-03-15_Enel_bolletta_gas.pdf"
    assert out.exists()
    assert (tmp_path / "originali/scan.pdf").exists()
    assert len(ctx.db.search("gas")) == 1

def test_invalid_doc_routed_to_dasmistare(tmp_path):
    src = tmp_path / "scan.pdf"; src.write_text("x")
    ctx = make_ctx(tmp_path, {"valido": False})
    process_file(src, ctx)
    files = list((tmp_path / "_DaSmistare").glob("0000-00-00_*.pdf"))
    assert len(files) == 1

def test_idempotent_skips_already_processed(tmp_path):
    src = tmp_path / "scan.pdf"; src.write_text("x")
    ctx = make_ctx(tmp_path, {
        "valido": True, "data": "2024-03-15", "mittente": "Enel",
        "tipo": "bolletta", "dettaglio": "gas",
        "categoria": "Casa/Utenze/Gas", "confidenza": "alta",
    })
    process_file(src, ctx)
    src2 = tmp_path / "scan2.pdf"; src2.write_text("x")
    result = process_file(src2, ctx)
    assert result == "skip"
    assert len(ctx.db.search("gas")) == 1

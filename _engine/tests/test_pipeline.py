import shutil
import zipfile
from pathlib import Path
from ocrsys.pipeline import process_file, plan_file, Context
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

    def fake_classify(t, taxonomy, mittenti_noti=None):
        return dict(classify_result)

    return Context(
        base=base, archivio=base / "archivio", da_smistare=base / "_DaSmistare",
        originali=base / "originali", text=base / "text",
        log_rinomine=base / "log_rinomine.csv",
        taxonomy=tax, db=db,
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
    # backup nello zip, nome interno con prefisso sha (F1)
    z = zipfile.ZipFile(tmp_path / "originali" / "originali.zip")
    assert sum(1 for n in z.namelist() if n.endswith("_scan.pdf")) == 1
    assert len(ctx.db.search("gas")) == 1

def test_backup_no_overwrite_on_same_name(tmp_path):
    # F1: due file DIVERSI con lo stesso nome -> entrambi salvati in originali
    ctx = make_ctx(tmp_path, {"valido": False})
    a = tmp_path / "IMG_0001.pdf"; a.write_text("contenuto A")
    process_file(a, ctx)
    # secondo file, stesso nome, contenuto diverso
    a.write_text("contenuto B DIVERSO")
    process_file(a, ctx)
    z = zipfile.ZipFile(tmp_path / "originali" / "originali.zip")
    names = [n for n in z.namelist() if n.endswith("_IMG_0001.pdf")]
    assert len(names) == 2
    contents = {z.read(n).decode() for n in names}
    assert contents == {"contenuto A", "contenuto B DIVERSO"}

def test_invalid_doc_routed_to_dasmistare(tmp_path):
    src = tmp_path / "scan.pdf"; src.write_text("x")
    ctx = make_ctx(tmp_path, {"valido": False})
    process_file(src, ctx)
    files = list((tmp_path / "_DaSmistare").glob("0000-00-00_*.pdf"))
    assert len(files) == 1

def test_dry_run_non_tocca_nulla(tmp_path):
    # plan_file calcola la destinazione SENZA spostare/scrivere/indicizzare
    src = tmp_path / "scan.pdf"; src.write_text("x")
    ctx = make_ctx(tmp_path, {
        "valido": True, "data": "2024-03-15", "mittente": "Enel",
        "tipo": "bolletta", "dettaglio": "gas",
        "categoria": "Casa/Utenze/Gas", "confidenza": "alta",
    })
    r = plan_file(src, ctx)
    assert r["status"] == "ok"
    assert r["dest"] == "archivio/Casa/Utenze/Gas/2024-03-15_Enel_bolletta_gas.pdf"
    # niente effetti collaterali
    assert list((tmp_path / "archivio").rglob("*.pdf")) == []
    assert list((tmp_path / "originali").iterdir()) == []
    assert ctx.db.search("gas") == []
    assert src.exists()

def test_conferma_puo_mandare_in_dasmistare(tmp_path):
    # un doc valido, ma la conferma lo dirotta in _DaSmistare
    src = tmp_path / "scan.pdf"; src.write_text("x")
    ctx = make_ctx(tmp_path, {
        "valido": True, "data": "2024-03-15", "mittente": "Enel",
        "tipo": "bolletta", "dettaglio": "gas",
        "categoria": "Casa/Utenze/Gas", "confidenza": "alta",
    })
    def conferma(nome, meta, data):
        meta["valido"] = False
        return meta, data
    status = process_file(src, ctx, conferma)
    assert status == "dasmistare"
    assert list((tmp_path / "_DaSmistare").glob("0000-00-00_*.pdf"))

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

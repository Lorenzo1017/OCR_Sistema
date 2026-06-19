from ocrsys.db import Database

def make_doc(**kw):
    base = dict(
        nome_file="2024-03-15_Enel_bolletta_gas.pdf",
        percorso="archivio/Casa/Utenze/Gas/2024-03-15_Enel_bolletta_gas.pdf",
        categoria="Casa/Utenze/Gas",
        data_documento="2024-03-15",
        mittente="Enel",
        tipo="bolletta",
        testo_completo="Fattura Enel gas marzo importo 50 euro",
        n_pagine=2,
        confidenza="alta",
        sha256="abc123",
    )
    base.update(kw)
    return base

def test_insert_and_search(tmp_path):
    db = Database(tmp_path / "index.db")
    db.insert(make_doc())
    results = db.search("gas")
    assert len(results) == 1
    assert results[0]["mittente"] == "Enel"

def test_already_processed(tmp_path):
    db = Database(tmp_path / "index.db")
    assert db.already_processed("abc123") is False
    db.insert(make_doc())
    assert db.already_processed("abc123") is True

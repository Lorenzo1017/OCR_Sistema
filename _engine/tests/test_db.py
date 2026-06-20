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

def test_search_caratteri_speciali_non_crasha(tmp_path):
    db = Database(tmp_path / "index.db")
    db.insert(make_doc())
    # query con caratteri che FTS5 interpreterebbe come sintassi
    for q in ['enel "bolletta', 'a/b', 'tariffa:', 'gas* (', 'a OR b', '- x']:
        assert isinstance(db.search(q), list)   # niente eccezioni
    # termine reale fra i caratteri speciali trova comunque
    assert len(db.search('"gas"')) == 1

def test_insert_ritorna_false_su_duplicato(tmp_path):
    db = Database(tmp_path / "index.db")
    assert db.insert(make_doc()) is True
    assert db.insert(make_doc()) is False   # stesso sha -> ignorato

def test_known_senders(tmp_path):
    db = Database(tmp_path / "index.db")
    db.insert(make_doc(sha256="a", mittente="Enel"))
    db.insert(make_doc(sha256="b", mittente="Enel"))
    db.insert(make_doc(sha256="c", mittente="Vodafone"))
    db.insert(make_doc(sha256="d", mittente=""))
    s = db.known_senders()
    assert s[0] == "Enel"          # più frequente prima
    assert "Vodafone" in s
    assert "" not in s             # vuoti esclusi

def test_record_error_increments(tmp_path):
    db = Database(tmp_path / "index.db")
    assert db.record_error("sha9", "scan.pdf", "boom") == 1
    assert db.record_error("sha9", "scan.pdf", "boom2") == 2
    assert db.record_error("sha9", "scan.pdf", "boom3") == 3
    # file diverso conta a parte
    assert db.record_error("altro", "x.pdf", "err") == 1

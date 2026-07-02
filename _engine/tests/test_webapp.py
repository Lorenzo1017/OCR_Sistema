import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import webapp
from ocrsys.db import Database


@pytest.fixture
def client(tmp_path, monkeypatch):
    base = tmp_path
    archivio = base / "archivio" / "Casa"
    archivio.mkdir(parents=True)
    f = archivio / "2023-02-02_Enel_bolletta_luce.pdf"
    f.write_bytes(b"%PDF test")
    (base / "_DaSmistare").mkdir()
    db_path = tmp_path / "t.db"
    db = Database(db_path)
    db.insert({"nome_file": f.name, "percorso": f"archivio/Casa/{f.name}",
               "categoria": "Casa", "data_documento": "2023-02-02",
               "mittente": "Enel", "tipo": "bolletta", "tags": "luce",
               "testo_completo": "bolletta della luce di febbraio",
               "n_pagine": 1, "confidenza": "alta", "sha256": "s1"})
    db.close()
    cat_yaml = tmp_path / "categorie.yaml"
    cat_yaml.write_text("Casa: []\nSalute:\n  Referti: []\n")
    monkeypatch.setattr(webapp.config, "BASE", base)
    monkeypatch.setattr(webapp.config, "ROOT", base)
    monkeypatch.setattr(webapp.config, "DB_PATH", db_path)
    monkeypatch.setattr(webapp.config, "DA_SMISTARE", base / "_DaSmistare")
    monkeypatch.setattr(webapp.config, "ARCHIVIO", base / "archivio")
    monkeypatch.setattr(webapp.config, "CATEGORIE_YAML", cat_yaml)
    monkeypatch.setattr(webapp.config, "CATEGORIE_PER_ANNO", ["Salute/Referti"])
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


def test_home_mostra_ultimi(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Enel" in r.data


def test_ricerca_trova(client):
    r = client.get("/?q=bolletta")
    assert b"1 risultati" in r.data and b"Enel" in r.data


def test_ricerca_nessun_risultato(client):
    r = client.get("/?q=inesistentexyz")
    assert b"0 risultati" in r.data


def test_sfoglia_albero_e_categoria(client):
    r = client.get("/sfoglia")
    assert b"Casa" in r.data
    r = client.get("/sfoglia?cat=Casa")
    assert b"Enel" in r.data


def test_stats(client):
    r = client.get("/stats")
    assert r.status_code == 200 and b"documenti" in r.data


def test_pdf_serve_file(client):
    r = client.get("/pdf/1")
    assert r.status_code == 200 and r.data.startswith(b"%PDF")


def test_pdf_inesistente_404(client):
    assert client.get("/pdf/999").status_code == 404


def test_csv_download(client):
    r = client.get("/csv")
    assert r.status_code == 200
    assert b"Enel" in r.data


def test_zip_categoria(client):
    r = client.get("/zip/categoria?cat=Casa")
    assert r.status_code == 200 and r.data[:2] == b"PK"


def test_zip_categoria_vuota_404(client):
    assert client.get("/zip/categoria?cat=Niente").status_code == 404


def test_doc_dettaglio_mostra_form(client):
    r = client.get("/doc/1")
    assert r.status_code == 200 and b"Salva" in r.data and b"Enel" in r.data


def test_doc_modifica_mittente_e_tags(client):
    r = client.post("/doc/1", data={"categoria": "Casa", "data": "2023-02-02",
                                    "mittente": "Enel Energia", "tipo": "bolletta",
                                    "tags": "luce febbraio"})
    assert b"Salvato" in r.data
    r = client.get("/?q=febbraio")     # FTS riallineato dopo l'update
    assert b"1 risultati" in r.data


def test_doc_cambio_categoria_sposta_file(client):
    import webapp as w
    r = client.post("/doc/1", data={"categoria": "Salute/Referti",
                                    "data": "2023-02-02", "mittente": "Enel",
                                    "tipo": "bolletta", "tags": "luce"})
    assert b"Salvato" in r.data
    # per-anno: Salute/Referti + data 2023 -> sottocartella 2023
    dest = w.config.ARCHIVIO / "Salute/Referti/2023"
    assert any(dest.glob("*.pdf"))
    # il vecchio file non esiste piu'
    assert not any((w.config.ARCHIVIO / "Casa").glob("*.pdf"))


def test_doc_data_invalida_non_salvata(client):
    r = client.post("/doc/1", data={"categoria": "Casa", "data": "31/31/2023",
                                    "mittente": "Enel", "tipo": "bolletta",
                                    "tags": ""})
    assert b"Data non valida" in r.data

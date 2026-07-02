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
    monkeypatch.setattr(webapp.config, "BASE", base)
    monkeypatch.setattr(webapp.config, "ROOT", base)
    monkeypatch.setattr(webapp.config, "DB_PATH", db_path)
    monkeypatch.setattr(webapp.config, "DA_SMISTARE", base / "_DaSmistare")
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

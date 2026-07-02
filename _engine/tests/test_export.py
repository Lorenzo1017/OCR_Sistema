import csv
import zipfile

import pytest

from ocrsys import export
from ocrsys.db import Database


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    base = tmp_path
    archivio = base / "archivio"
    (archivio / "Salute/Referti/2024").mkdir(parents=True)
    (archivio / "Casa").mkdir(parents=True)
    f1 = archivio / "Salute/Referti/2024/2024-01-01_Osp_referto_x.pdf"
    f1.write_bytes(b"%PDF a")
    f2 = archivio / "Casa/2023-02-02_Enel_bolletta_luce.pdf"
    f2.write_bytes(b"%PDF b")
    monkeypatch.setattr(export.config, "BASE", base)
    monkeypatch.setattr(export.config, "ROOT", base)
    monkeypatch.setattr(export.config, "ARCHIVIO", archivio)
    db = Database(tmp_path / "test.db")
    db.insert({"nome_file": f1.name, "percorso": "archivio/Salute/Referti/2024/" + f1.name,
               "categoria": "Salute/Referti", "data_documento": "2024-01-01",
               "mittente": "Osp", "tipo": "referto", "tags": "sangue",
               "testo_completo": "esame del sangue", "n_pagine": 1,
               "confidenza": "alta", "sha256": "s1"})
    db.insert({"nome_file": f2.name, "percorso": "archivio/Casa/" + f2.name,
               "categoria": "Casa", "data_documento": "2023-02-02",
               "mittente": "Enel", "tipo": "bolletta", "tags": "luce",
               "testo_completo": "bolletta della luce", "n_pagine": 1,
               "confidenza": "alta", "sha256": "s2"})
    yield db, base
    db.close()


def test_indice_csv(ambiente, tmp_path):
    db, base = ambiente
    dest = export.indice_csv(db, tmp_path / "indice.csv")
    with open(dest, encoding="utf-8-sig") as f:
        righe = list(csv.reader(f, delimiter=";"))
    assert righe[0][0] == "data_documento"
    assert len(righe) == 3          # header + 2 documenti
    assert any("Enel" in r for r in righe[1] + righe[2])


def test_zip_categoria_include_sottocartelle_anno(ambiente, tmp_path):
    db, base = ambiente
    dest, agg, man = export.zip_categoria(db, "Salute/Referti", tmp_path / "c.zip")
    assert agg == 1 and man == 0
    with zipfile.ZipFile(dest) as z:
        assert any("2024" in n for n in z.namelist())


def test_zip_categoria_vuota(ambiente, tmp_path):
    db, base = ambiente
    dest, agg, man = export.zip_categoria(db, "Inesistente", tmp_path / "v.zip")
    assert dest is None


def test_zip_ricerca(ambiente, tmp_path):
    db, base = ambiente
    dest, agg, man = export.zip_ricerca(db, "bolletta", tmp_path / "r.zip")
    assert agg == 1
    with zipfile.ZipFile(dest) as z:
        assert any("Enel" in n for n in z.namelist())


def test_backup_completo(ambiente, tmp_path, monkeypatch):
    db, base = ambiente
    monkeypatch.setattr(export.config, "DB_PATH", tmp_path / "test.db")
    dest = export.backup_completo(tmp_path / "b.zip")
    with zipfile.ZipFile(dest) as z:
        nomi = z.namelist()
    assert sum(1 for n in nomi if n.endswith(".pdf")) == 2
    assert any(n.endswith("test.db") for n in nomi)

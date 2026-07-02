import pytest

from ocrsys import semantic
from ocrsys.db import Database


@pytest.fixture
def db(tmp_path):
    d = Database(tmp_path / "t.db")
    d.insert({"nome_file": "a.pdf", "percorso": "archivio/a.pdf",
              "categoria": "Salute", "data_documento": "2024-01-01",
              "mittente": "Dentista Rossi", "tipo": "fattura",
              "tags": "odontoiatra", "testo_completo": "fattura odontoiatra " * 5,
              "n_pagine": 1, "confidenza": "alta", "sha256": "sha_dente"})
    d.insert({"nome_file": "b.pdf", "percorso": "archivio/b.pdf",
              "categoria": "Casa", "data_documento": "2023-01-01",
              "mittente": "Enel", "tipo": "bolletta",
              "tags": "luce", "testo_completo": "bolletta energia elettrica " * 5,
              "n_pagine": 1, "confidenza": "alta", "sha256": "sha_luce"})
    yield d
    d.close()


def _finto_embed(mapping):
    def f(testo):
        for chiave, vec in mapping.items():
            if chiave in testo.lower():
                return vec
        return [0.0, 0.0, 1.0]
    return f


def test_indicizza_e_cerca_per_significato(db, monkeypatch):
    # 'dentista/odontoiatra' -> asse X, 'luce/energia' -> asse Y
    monkeypatch.setattr(semantic, "embed", _finto_embed({
        "odontoiatra": [1.0, 0.1, 0.0],
        "energia": [0.1, 1.0, 0.0],
        "dentista": [0.9, 0.2, 0.0],       # query simile a odontoiatra
    }))
    n = semantic.indicizza(db)
    assert n == 2
    ris = semantic.cerca(db, "spese dentista", k=2)
    assert ris[0]["sha256"] == "sha_dente"      # il piu' simile per significato
    assert ris[0]["punteggio"] > ris[1]["punteggio"]


def test_indicizza_idempotente(db, monkeypatch):
    monkeypatch.setattr(semantic, "embed", lambda t: [1.0, 0.0])
    assert semantic.indicizza(db) == 2
    assert semantic.indicizza(db) == 0          # gia' tutti indicizzati


def test_cerca_senza_indice_vuota(db, monkeypatch):
    monkeypatch.setattr(semantic, "embed", lambda t: [1.0, 0.0])
    assert semantic.cerca(db, "qualsiasi") == []


def test_coseno():
    assert semantic._coseno([1, 0], [1, 0]) == pytest.approx(1.0)
    assert semantic._coseno([1, 0], [0, 1]) == pytest.approx(0.0)
    assert semantic._coseno([0, 0], [1, 1]) == 0.0

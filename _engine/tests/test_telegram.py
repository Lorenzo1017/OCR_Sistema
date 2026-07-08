from ocrsys import telegram
from ocrsys.db import Database


def test_comando_parsing():
    assert telegram.comando("/cerca mutuo 2024") == ("cerca", "mutuo 2024")
    assert telegram.comando("/stato") == ("stato", "")
    assert telegram.comando("/cerca@MioBot ciao") == ("cerca", "ciao")
    assert telegram.comando("ciao") == ("", "")
    assert telegram.comando("") == ("", "")


def test_autorizzazione():
    cfg = {"chat_id": [12345]}
    assert telegram.autorizzato(12345, cfg) is True
    assert telegram.autorizzato("12345", cfg) is True     # stringa o int
    assert telegram.autorizzato(999, cfg) is False
    assert telegram.autorizzato(12345, {}) is False       # nessuna whitelist -> nega


def test_risposta_cerca_e_pdf(tmp_path):
    db = Database(tmp_path / "t.db")
    for i in range(2):
        db.insert({"nome_file": f"doc{i}.pdf", "percorso": f"archivio/doc{i}.pdf",
                   "categoria": "Casa", "data_documento": f"2024-01-0{i+1}",
                   "mittente": "Enel", "tipo": "bolletta", "tags": "luce",
                   "testo_completo": "bolletta luce parolachiave",
                   "n_pagine": 1, "confidenza": "alta", "sha256": f"s{i}"})
    testo, pdf = telegram.risposta(db, "/cerca parolachiave")
    assert "risultati" in testo and "doc0.pdf" in testo
    assert pdf and all(p.startswith("archivio/") for p in pdf)
    db.close()


def test_risposta_stato_e_aiuto(tmp_path):
    db = Database(tmp_path / "t.db")
    db.insert({"nome_file": "a.pdf", "percorso": "archivio/a.pdf",
               "categoria": "Casa", "data_documento": "2024-01-01",
               "mittente": "x", "tipo": "y", "tags": "", "testo_completo": "t",
               "n_pagine": 1, "confidenza": "bassa", "sha256": "s1"})
    st, pdf = telegram.risposta(db, "/stato")
    assert "1 documenti" in st and "1 da rivedere" in st and pdf == []
    aiuto, _ = telegram.risposta(db, "/start")
    assert "/cerca" in aiuto
    db.close()


def test_cerca_senza_risultati(tmp_path):
    db = Database(tmp_path / "t.db")
    testo, pdf = telegram.risposta(db, "/cerca inesistente")
    assert "Nessun documento" in testo and pdf == []
    db.close()

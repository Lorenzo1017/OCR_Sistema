import pytest

from ocrsys import dedup
from ocrsys.db import Database


_LUNGO = ("Contratto di locazione a uso abitativo stipulato tra le parti in "
          "data odierna con tutte le clausole relative a canone deposito durata "
          "e obblighi delle parti secondo la normativa vigente numero " * 3)


def test_firma_uguale_per_testo_equivalente():
    a = dedup.firma_testo(_LUNGO)
    b = dedup.firma_testo(_LUNGO.upper().replace(" ", "   "))
    assert a and a == b               # punteggiatura/spazi/maiuscole non contano


def test_firma_vuota_se_testo_scarso():
    # testo corto (etichetta generica) NON ottiene firma: evita falsi positivi
    assert dedup.firma_testo("Esame di laboratorio per Sig CHIEREGATO") == ""
    assert dedup.firma_testo("ciao") == ""
    assert dedup.firma_testo("") == ""


def _doc(sha, testo, pagine, cat="Casa"):
    return {"nome_file": f"{sha}.pdf", "percorso": f"archivio/{sha}.pdf",
            "categoria": cat, "data_documento": "2024-01-01", "mittente": "x",
            "tipo": "y", "tags": "", "testo_completo": testo, "n_pagine": pagine,
            "confidenza": "alta", "sha256": sha,
            "firma": dedup.firma_testo(testo)}


def test_tiene_il_piu_corposo(tmp_path, monkeypatch):
    monkeypatch.setattr(dedup.config, "BASE", tmp_path)
    monkeypatch.setattr(dedup.config, "DUPLICATI", tmp_path / "duplicati")
    arch = tmp_path / "archivio"; arch.mkdir()
    (arch / "corto.pdf").write_bytes(b"x")
    (arch / "lungo.pdf").write_bytes(b"xxxxx")
    db = Database(tmp_path / "t.db")
    # stesso contenuto (stessa firma), ma d2 ha piu' pagine -> piu' corposo
    d1 = _doc("corto", _LUNGO, 1); d1["nome_file"] = "corto.pdf"; d1["percorso"] = "archivio/corto.pdf"
    d2 = _doc("lungo", _LUNGO, 3); d2["nome_file"] = "lungo.pdf"; d2["percorso"] = "archivio/lungo.pdf"
    db.insert(d1); db.insert(d2)
    mossi = dedup.dedup_tutto(db)
    assert mossi == 1
    rimasti = [r[0] for r in db.conn.execute("SELECT nome_file FROM documenti")]
    assert rimasti == ["lungo.pdf"]                 # tenuto il piu' corposo
    assert (tmp_path / "duplicati" / "corto.pdf").exists()  # l'altro spostato
    assert not (arch / "corto.pdf").exists()
    db.close()


def test_niente_duplicati_nessuna_azione(tmp_path, monkeypatch):
    monkeypatch.setattr(dedup.config, "BASE", tmp_path)
    (tmp_path / "archivio").mkdir()
    db = Database(tmp_path / "t.db")
    db.insert(_doc("a", _LUNGO, 1))
    db.insert(_doc("b", _LUNGO.replace("locazione", "vendita") + " differente x", 1))
    assert dedup.dedup_tutto(db) == 0     # firme diverse -> nessuna azione
    db.close()


def test_backfill_firme(tmp_path, monkeypatch):
    monkeypatch.setattr(dedup.config, "BASE", tmp_path)
    db = Database(tmp_path / "t.db")
    doc = _doc("a", _LUNGO, 1)
    doc["firma"] = None
    db.conn.execute("INSERT INTO documenti (nome_file,percorso,categoria,"
                    "data_documento,mittente,tipo,tags,testo_completo,n_pagine,"
                    "confidenza,sha256,firma) VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(doc.get(k) for k in ("nome_file","percorso","categoria",
                    "data_documento","mittente","tipo","tags","testo_completo",
                    "n_pagine","confidenza","sha256","firma")))
    db.conn.commit()
    assert dedup.backfill_firme(db) == 1
    f = db.conn.execute("SELECT firma FROM documenti").fetchone()[0]
    assert f
    db.close()

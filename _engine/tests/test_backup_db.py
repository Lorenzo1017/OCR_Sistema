import sqlite3

import backup_db
from ocrsys.db import Database


def _prepara(tmp_path, monkeypatch):
    root = tmp_path
    (root / "esportazioni").mkdir()
    db_path = root / "index.db"
    d = Database(db_path)
    d.insert({"nome_file": "a.pdf", "percorso": "archivio/a.pdf",
              "categoria": "Casa", "data_documento": "2024-01-01",
              "mittente": "Enel", "tipo": "x", "tags": "", "testo_completo": "t",
              "n_pagine": 1, "confidenza": "alta", "sha256": "s1"})
    d.close()
    cat = root / "categorie.yaml"; cat.write_text("Casa: []\n")
    imp = root / "impostazioni.yaml"; imp.write_text("ocr_lingue: ita\n")
    monkeypatch.setattr(backup_db.config, "ROOT", root)
    monkeypatch.setattr(backup_db.config, "DB_PATH", db_path)
    monkeypatch.setattr(backup_db.config, "CATEGORIE_YAML", cat)
    monkeypatch.setattr(backup_db.config, "IMPOSTAZIONI_YAML", imp)
    return root


def test_snapshot_consistente_e_leggibile(tmp_path, monkeypatch):
    _prepara(tmp_path, monkeypatch)
    dest = backup_db.esegui(tieni=7, oggi="2026-07-02")
    assert dest.exists()
    c = sqlite3.connect(str(dest))
    n = c.execute("SELECT COUNT(*) FROM documenti").fetchone()[0]
    c.close()
    assert n == 1                      # il backup contiene i dati
    # la configurazione e' allegata
    assert (dest.parent / "2026-07-02_categorie.yaml").exists()


def test_rotazione_tiene_solo_ultimi_n(tmp_path, monkeypatch):
    _prepara(tmp_path, monkeypatch)
    for g in ("2026-06-28", "2026-06-29", "2026-06-30", "2026-07-01"):
        backup_db.esegui(tieni=2, oggi=g)
    rimasti = sorted(p.name for p in backup_db._dir().glob("index_*.db"))
    assert rimasti == ["index_2026-06-30.db", "index_2026-07-01.db"]
    # anche gli yaml vecchi vengono rimossi
    assert not list(backup_db._dir().glob("2026-06-28_*"))

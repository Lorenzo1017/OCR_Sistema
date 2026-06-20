import shutil
from ocrsys import preflight, config


def test_segnala_tool_mancante(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _x: None)
    monkeypatch.setattr(config, "CATEGORIE_YAML", tmp_path / "categorie.yaml")
    problemi = preflight.check()
    testo = " ".join(problemi)
    assert "tesseract" in testo
    assert "ocrmypdf" in testo
    assert "ollama" in testo
    assert "categorie" in testo.lower()


def test_ok_quando_tutto_presente(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _x: "/usr/bin/" + _x)
    cat = tmp_path / "categorie.yaml"
    cat.write_text("Casa:\n  Utenze: []\n")
    monkeypatch.setattr(config, "CATEGORIE_YAML", cat)
    assert preflight.check() == []

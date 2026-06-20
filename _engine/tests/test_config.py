from ocrsys import config


def test_leggi_impostazioni_assente(tmp_path):
    assert config.leggi_impostazioni(tmp_path / "manca.yaml") == {}


def test_leggi_impostazioni_lingue(tmp_path):
    f = tmp_path / "impostazioni.yaml"
    f.write_text("ocr_lingue: ita+eng\n")
    assert config.leggi_impostazioni(f).get("ocr_lingue") == "ita+eng"


def test_leggi_impostazioni_yaml_rotto(tmp_path):
    f = tmp_path / "impostazioni.yaml"
    f.write_text(":: non valido :::\n")
    assert config.leggi_impostazioni(f) == {}   # non solleva

from ocrsys import prompts


def test_riempi_sostituisce_solo_i_segnaposti():
    t = 'schema {"a":1} e {categorie} qui'
    out = prompts.riempi(t, categorie="CAT")
    assert out == 'schema {"a":1} e CAT qui'   # le graffe JSON restano intatte


def test_carica_materializza_default(tmp_path, monkeypatch):
    monkeypatch.setattr(prompts.config, "PROMPTS_DIR", tmp_path / "prompts")
    out = prompts.carica("classificazione.txt", "DEFAULT XYZ")
    assert out == "DEFAULT XYZ"
    # il file e' stato creato per l'editing
    f = tmp_path / "prompts" / "classificazione.txt"
    assert f.exists() and f.read_text() == "DEFAULT XYZ"


def test_carica_usa_il_file_se_presente(tmp_path, monkeypatch):
    d = tmp_path / "prompts"; d.mkdir()
    (d / "vision.txt").write_text("PROMPT PERSONALIZZATO")
    monkeypatch.setattr(prompts.config, "PROMPTS_DIR", d)
    assert prompts.carica("vision.txt", "DEFAULT") == "PROMPT PERSONALIZZATO"


def test_classify_build_prompt_funziona_ancora(tmp_path, monkeypatch):
    # il prompt di classificazione si costruisce senza errori di format
    from ocrsys import classify
    from ocrsys.taxonomy import Taxonomy
    monkeypatch.setattr(prompts.config, "PROMPTS_DIR", tmp_path / "p")
    tax = Taxonomy({"Casa": {"Utenze": {}}})
    p = classify._build_prompt("testo di prova", tax, ["Enel"])
    assert "Casa/Utenze" in p and "testo di prova" in p and '"data"' in p

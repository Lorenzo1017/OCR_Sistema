from ocrsys.taxonomy import Taxonomy

YAML = """
Casa:
  Utenze: [Gas, Luce]
  Condominio: []
Salute:
  Referti: []
Acquisti-Garanzie: []
"""

def test_valid_paths_flatten(tmp_path):
    f = tmp_path / "categorie.yaml"
    f.write_text(YAML)
    t = Taxonomy.load(f)
    paths = t.valid_paths()
    assert "Casa/Utenze/Gas" in paths
    assert "Casa/Utenze/Luce" in paths
    assert "Casa/Condominio" in paths
    assert "Salute/Referti" in paths
    assert "Acquisti-Garanzie" in paths

def test_is_valid(tmp_path):
    f = tmp_path / "categorie.yaml"
    f.write_text(YAML)
    t = Taxonomy.load(f)
    assert t.is_valid("Casa/Utenze/Gas") is True
    assert t.is_valid("Casa/Inventata") is False
    assert t.is_valid("") is False

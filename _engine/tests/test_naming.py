from ocrsys.naming import build_name, resolve_collision

def test_build_name_basic():
    n = build_name("2024-03-15", "Enel", "bolletta", "gas")
    assert n == "2024-03-15_Enel_bolletta_gas.pdf"

def test_build_name_sanitizes():
    n = build_name("2024-03-15", "A.S.L. Roma/2", "referto", "esami del sangue")
    assert n == "2024-03-15_ASL-Roma2_referto_esami-del-sangue.pdf"

def test_build_name_missing_date():
    n = build_name(None, "Ignoto", "documento", "")
    assert n.startswith("0000-00-00_")
    assert n.endswith(".pdf")

def test_build_name_rejects_non_iso_date():
    # data con slash (es. da Qwen) non deve mai entrare nel nome / spaccare il path
    n = build_name("15/03/2024", "Enel", "bolletta", "gas")
    assert "/" not in n
    assert n.startswith("0000-00-00_")

def test_resolve_collision(tmp_path):
    (tmp_path / "2024-03-15_Enel_bolletta_gas.pdf").write_text("x")
    name = "2024-03-15_Enel_bolletta_gas.pdf"
    assert resolve_collision(tmp_path, name) == "2024-03-15_Enel_bolletta_gas_v2.pdf"

def test_resolve_collision_none(tmp_path):
    assert resolve_collision(tmp_path, "nuovo.pdf") == "nuovo.pdf"

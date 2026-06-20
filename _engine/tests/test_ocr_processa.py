from ocrsys import runner
from ocrsys import config


def test_quarantena_moves_file(tmp_path, monkeypatch):
    errori_dir = tmp_path / "_DaSmistare" / "_errori"
    monkeypatch.setattr(config, "DA_SMISTARE_ERRORI", errori_dir)
    f = tmp_path / "rotto.pdf"
    f.write_text("xx")
    runner._quarantena(f)
    assert not f.exists()
    assert (errori_dir / "rotto.pdf").exists()


def test_quarantena_no_overwrite(tmp_path, monkeypatch):
    errori_dir = tmp_path / "_DaSmistare" / "_errori"
    monkeypatch.setattr(config, "DA_SMISTARE_ERRORI", errori_dir)
    for _ in range(2):
        f = tmp_path / "rotto.pdf"
        f.write_text("xx")
        runner._quarantena(f)
    assert (errori_dir / "rotto.pdf").exists()
    assert (errori_dir / "rotto_v2.pdf").exists()

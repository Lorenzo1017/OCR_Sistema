from ocrsys.runner import _prune_dirs_vuote


def test_rimuove_vuote_tiene_piene(tmp_path):
    (tmp_path / "vuota").mkdir()
    (tmp_path / "vuota_annidata" / "dentro").mkdir(parents=True)
    piena = tmp_path / "piena"
    piena.mkdir()
    (piena / "resta.zip").write_text("x")

    rimosse = _prune_dirs_vuote(tmp_path)

    assert not (tmp_path / "vuota").exists()
    assert not (tmp_path / "vuota_annidata").exists()   # genitore svuotato a cascata
    assert piena.exists() and (piena / "resta.zip").exists()
    assert rimosse == 3   # vuota + dentro + vuota_annidata
    assert tmp_path.exists()                            # root mai rimossa


def test_ds_store_considerata_vuota(tmp_path):
    d = tmp_path / "solo_dsstore"
    d.mkdir()
    (d / ".DS_Store").write_text("junk")
    _prune_dirs_vuote(tmp_path)
    assert not d.exists()

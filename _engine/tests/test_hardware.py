from ocrsys import hardware


def test_ram_bassa_e_problema():
    rep = {"os": "X", "cpu": 8, "ram_gb": 4, "disk_free_gb": 100}
    problemi, _ = hardware.valuta(rep)
    assert any("RAM" in p for p in problemi)


def test_ram_media_e_avviso():
    rep = {"os": "X", "cpu": 8, "ram_gb": 12, "disk_free_gb": 100}
    problemi, avvisi = hardware.valuta(rep)
    assert problemi == []
    assert any("RAM" in a for a in avvisi)


def test_hardware_adeguato_nessun_problema():
    rep = {"os": "X", "cpu": 8, "ram_gb": 32, "disk_free_gb": 200}
    problemi, avvisi = hardware.valuta(rep)
    assert problemi == []
    assert avvisi == []


def test_disco_pieno_e_problema():
    rep = {"os": "X", "cpu": 8, "ram_gb": 32, "disk_free_gb": 3}
    problemi, _ = hardware.valuta(rep)
    assert any("disco" in p.lower() or "spazio" in p.lower() for p in problemi)


def test_cpu_pochi_core_avviso():
    rep = {"os": "X", "cpu": 2, "ram_gb": 32, "disk_free_gb": 200}
    _, avvisi = hardware.valuta(rep)
    assert any("core" in a.lower() for a in avvisi)


def test_valori_mancanti_non_crasha():
    rep = {"os": "X", "cpu": None, "ram_gb": None, "disk_free_gb": None}
    problemi, avvisi = hardware.valuta(rep)
    assert problemi == [] and avvisi == []

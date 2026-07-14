from ocrsys import scanner_lock


def test_rileva_app_configurata(monkeypatch):
    monkeypatch.setattr(scanner_lock.config, "PAUSA_APP", ["Image Capture"])
    monkeypatch.setattr(scanner_lock, "_processo_attivo",
                        lambda n: n == "Image Capture")
    assert scanner_lock.app_scanner_attiva() == "Image Capture"


def test_nessuna_app_attiva(monkeypatch):
    monkeypatch.setattr(scanner_lock.config, "PAUSA_APP", ["Image Capture"])
    monkeypatch.setattr(scanner_lock, "_processo_attivo", lambda n: False)
    assert scanner_lock.app_scanner_attiva() is None


def test_lista_vuota_non_blocca(monkeypatch):
    monkeypatch.setattr(scanner_lock.config, "PAUSA_APP", [])
    assert scanner_lock.app_scanner_attiva() is None


def test_run_once_in_pausa_con_scanner(monkeypatch, tmp_path):
    # run_once deve uscire subito, senza toccare inbox, se lo scanner e' aperto
    from ocrsys import runner
    monkeypatch.setattr(runner.config, "INBOX", tmp_path / "inbox")
    monkeypatch.setattr(runner.config, "ARCHIVIO", tmp_path / "archivio")
    monkeypatch.setattr(runner.config, "DA_SMISTARE", tmp_path / "_DaSmistare")
    monkeypatch.setattr(runner.config, "ORIGINALI", tmp_path / "orig")
    monkeypatch.setattr(runner.config, "TEXT", tmp_path / "text")
    monkeypatch.setattr(runner.scanner_lock, "app_scanner_attiva",
                        lambda: "Image Capture")
    # se entrasse nella pipeline chiamerebbe preflight; lo facciamo fallire per
    # dimostrare che NON ci arriva (esce prima per via dello scanner)
    monkeypatch.setattr(runner.preflight, "check",
                        lambda: (_ for _ in ()).throw(AssertionError("non deve arrivarci")))
    msg = runner.run_once(stampa=False, notifiche=False)
    assert "pausa" in msg.lower() and "Image Capture" in msg

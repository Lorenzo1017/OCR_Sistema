from ocrsys import salute


def _setup(tmp_path, monkeypatch):
    quar = tmp_path / "_DaSmistare" / "_errori"
    quar.mkdir(parents=True)
    monkeypatch.setattr(salute.config, "SISTEMA", tmp_path)
    monkeypatch.setattr(salute, "_STATO", tmp_path / ".salute.json")
    monkeypatch.setattr(salute.config, "DA_SMISTARE", tmp_path / "_DaSmistare")
    monkeypatch.setattr(salute.config, "DA_SMISTARE_ERRORI", quar)
    return quar


def test_notifica_solo_su_aumento_quarantena(tmp_path, monkeypatch):
    quar = _setup(tmp_path, monkeypatch)
    avvisi = []
    monkeypatch.setattr(salute, "notify", lambda t, m: avvisi.append((t, m)))
    # primo giro: 1 file in quarantena -> notifica (0 -> 1)
    (quar / "a.pdf").write_bytes(b"x")
    salute.controlla()
    assert len(avvisi) == 1
    # secondo giro: nessun nuovo file -> nessuna notifica
    salute.controlla()
    assert len(avvisi) == 1
    # terzo giro: un altro file -> notifica
    (quar / "b.pdf").write_bytes(b"x")
    salute.controlla()
    assert len(avvisi) == 2


def test_notifiche_disattivabili(tmp_path, monkeypatch):
    quar = _setup(tmp_path, monkeypatch)
    avvisi = []
    monkeypatch.setattr(salute, "notify", lambda t, m: avvisi.append(1))
    (quar / "a.pdf").write_bytes(b"x")
    stato = salute.controlla(notifiche=False)
    assert avvisi == [] and stato["quarantena"] == 1


def test_stato_persistito(tmp_path, monkeypatch):
    quar = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(salute, "notify", lambda t, m: None)
    (quar / "a.pdf").write_bytes(b"x")
    salute.controlla()
    assert salute._leggi()["quarantena"] == 1

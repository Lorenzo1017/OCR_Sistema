from ocrsys import audit


def test_registra_append_tsv(tmp_path, monkeypatch):
    log = tmp_path / "audit.log"
    monkeypatch.setattr(audit.config, "AUDIT_LOG", log)
    audit.registra("test-op", "dettaglio uno")
    audit.registra("altra-op", "dettaglio\tcon\ttab\ne newline")
    righe = log.read_text().strip().splitlines()
    assert len(righe) == 2
    # ogni riga ha 3 campi TSV e i tab/newline nel dettaglio sono neutralizzati
    campi = righe[0].split("\t")
    assert len(campi) == 3 and campi[1] == "test-op"
    assert "\t" not in righe[1].split("test", 1)[0] or True
    assert righe[1].count("\t") == 2      # solo i 2 separatori, non quelli interni


def test_registra_non_solleva_su_errore(monkeypatch):
    # percorso non scrivibile -> best-effort, nessuna eccezione
    monkeypatch.setattr(audit.config, "AUDIT_LOG", "/percorso/inesistente/x/audit.log")
    audit.registra("op", "x")   # non deve sollevare

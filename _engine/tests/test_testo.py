from ocrsys import testo


def test_rimuove_header_ripetuto(monkeypatch):
    monkeypatch.setattr(testo.config, "RIMUOVI_REGEX", [])
    t = ("ACME SPA - Via Roma 1\n"
         "Contenuto pagina uno molto importante da classificare bene.\n"
         "ACME SPA - Via Roma 1\n"
         "Contenuto pagina due con altri dettagli utili al modello.\n"
         "ACME SPA - Via Roma 1\n"
         "Chiusura del documento con la firma finale del responsabile.\n")
    out = testo.pulisci(t)
    # l'intestazione ripetuta 3 volte compare al massimo 2 volte
    assert out.count("ACME SPA - Via Roma 1") <= 2
    assert "Contenuto pagina uno" in out and "Chiusura del documento" in out


def test_rimuove_numeri_pagina_e_separatori(monkeypatch):
    monkeypatch.setattr(testo.config, "RIMUOVI_REGEX", [])
    t = "Testo utile del referto medico completo e leggibile.\nPag. 1/3\n-----\n2 / 3"
    out = testo.pulisci(t)
    assert "Pag. 1/3" not in out and "-----" not in out and "2 / 3" not in out
    assert "referto medico" in out


def test_regex_utente(monkeypatch):
    monkeypatch.setattr(testo.config, "RIMUOVI_REGEX",
                        [r"Azienda certificata ISO.*"])
    t = ("Azienda certificata ISO 9001 45001 14001\n"
         "Oggetto: attivazione impianto fotovoltaico presso il cliente.\n")
    out = testo.pulisci(t)
    assert "ISO 9001" not in out
    assert "attivazione impianto" in out


def test_fallback_se_resta_troppo_poco(monkeypatch):
    monkeypatch.setattr(testo.config, "RIMUOVI_REGEX", [r".*"])
    t = "Poco testo ma da tenere comunque."
    # la regex cancellerebbe tutto -> ritorna l'originale
    assert testo.pulisci(t) == t


def test_testo_vuoto(monkeypatch):
    monkeypatch.setattr(testo.config, "RIMUOVI_REGEX", [])
    assert testo.pulisci("") == ""

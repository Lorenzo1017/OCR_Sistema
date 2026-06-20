from ocrsys.classify import parse_response, valuta_utenza, _build_prompt
from ocrsys.taxonomy import Taxonomy

TAX = Taxonomy({"Casa/Utenze/Gas", "Salute/Referti"})

def test_build_prompt_include_mittenti_noti():
    p = _build_prompt("testo", TAX, ["Enel", "Vodafone"])
    assert "Enel" in p and "Vodafone" in p
    assert "Mittenti gia' visti" in p

def test_build_prompt_senza_mittenti():
    p = _build_prompt("testo", TAX, None)
    assert "Mittenti gia' visti" not in p
    assert "Casa/Utenze/Gas" in p   # categorie sempre presenti

def test_valuta_utenza_autocorregge_acqua_da_luce():
    # bolletta acqua (con 1 riga boilerplate "energia elettrica") messa in Luce
    txt = ("Acque Venete fornitura idrica acqua acque depurazione fognatura "
           "consumo acqua. Non comprende energia elettrica.")
    nuova, ok = valuta_utenza("Casa/Utenze/Luce", txt)
    assert ok is True
    assert nuova == "Casa/Utenze/Acqua"   # dominanza netta -> corretto

def test_valuta_utenza_no_falso_positivo_gasolio():
    # "gasolio" non deve contare come Gas; "automobile" non come Telefono(mobile)
    txt = "rifornimento gasolio per automobile, nessuna utenza domestica"
    nuova, ok = valuta_utenza("Casa/Utenze/Gas", txt)
    # nessun riscontro reale di utenza -> fiducia al modello, invariato
    assert (nuova, ok) == ("Casa/Utenze/Gas", True)

def test_valuta_utenza_scelta_coerente_invariata():
    txt = "Enel gas naturale consumo 142 Smc gas"
    assert valuta_utenza("Casa/Utenze/Gas", txt) == ("Casa/Utenze/Gas", True)

def test_valuta_utenza_non_utenza_passa():
    assert valuta_utenza("Salute/Referti", "qualsiasi testo") == ("Salute/Referti", True)

def test_valuta_utenza_nessun_segnale_fiducia_al_modello():
    assert valuta_utenza("Casa/Utenze/Gas", "documento generico") == ("Casa/Utenze/Gas", True)

def test_valuta_utenza_mismatch_ambiguo_a_dasmistare():
    # un solo accenno a un'altra utenza, non dominante -> _DaSmistare
    txt = "fattura con un riferimento ad acqua una volta"
    nuova, ok = valuta_utenza("Casa/Utenze/Gas", txt)
    assert ok is False

def test_parse_normalizza_categoria_con_spazi():
    raw = '{"data":"2024-03-15","mittente":"Enel","tipo":"bolletta",' \
          '"dettaglio":"gas","categoria":" Casa/Utenze/Gas ","confidenza":"Alta"}'
    r = parse_response(raw, TAX)
    assert r["categoria"] == "Casa/Utenze/Gas"
    assert r["valido"] is True   # spazi + "Alta" maiuscolo normalizzati

def test_parse_valid():
    raw = '{"data":"2024-03-15","mittente":"Enel","tipo":"bolletta",' \
          '"dettaglio":"gas","categoria":"Casa/Utenze/Gas","confidenza":"alta"}'
    r = parse_response(raw, TAX)
    assert r["categoria"] == "Casa/Utenze/Gas"
    assert r["mittente"] == "Enel"
    assert r["valido"] is True

def test_parse_invalid_category_falls_to_dasmistare():
    raw = '{"data":"2024-03-15","mittente":"X","tipo":"y",' \
          '"dettaglio":"z","categoria":"Inventata/Ramo","confidenza":"alta"}'
    r = parse_response(raw, TAX)
    assert r["valido"] is False

def test_parse_garbage_falls_to_dasmistare():
    r = parse_response("non e json", TAX)
    assert r["valido"] is False

def test_parse_extracts_json_from_noise():
    raw = 'Ecco il risultato:\n{"data":"2023-01-02","mittente":"ASL",' \
          '"tipo":"referto","dettaglio":"","categoria":"Salute/Referti",' \
          '"confidenza":"media"}\nFine.'
    r = parse_response(raw, TAX)
    assert r["valido"] is True
    assert r["categoria"] == "Salute/Referti"

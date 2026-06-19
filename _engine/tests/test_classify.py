from ocrsys.classify import parse_response
from ocrsys.taxonomy import Taxonomy

TAX = Taxonomy({"Casa/Utenze/Gas", "Salute/Referti"})

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

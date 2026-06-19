from ocrsys.dates import extract_date, normalize_date

def test_normalize_already_iso():
    assert normalize_date("2024-03-15") == "2024-03-15"

def test_normalize_italian_slash():
    assert normalize_date("15/03/2024") == "2024-03-15"

def test_normalize_short_year():
    assert normalize_date("15.03.24") == "2024-03-15"

def test_normalize_empty_and_garbage():
    assert normalize_date("") is None
    assert normalize_date(None) is None
    assert normalize_date("non una data") is None

def test_normalize_invalid_iso_ranges():
    assert normalize_date("2024-13-40") is None

def test_numeric_slash():
    assert extract_date("Fattura del 15/03/2024 importo 50 euro") == "2024-03-15"

def test_numeric_dots_short_year():
    assert extract_date("Data 15.03.24") == "2024-03-15"

def test_italian_month_name():
    assert extract_date("Bologna, 8 novembre 2023") == "2023-11-08"

def test_no_date_returns_none():
    assert extract_date("Nessuna data qui presente") is None

def test_picks_earliest_plausible_when_multiple():
    txt = "Emessa il 15/03/2024. Scadenza pagamento 30/04/2024."
    assert extract_date(txt) == "2024-03-15"

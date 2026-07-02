from pathlib import Path

from ocrsys.naming import dir_categoria, strip_anno

ARCH = Path("/x/archivio")
PER_ANNO = ["Salute/Referti"]


def test_categoria_per_anno_con_data():
    d = dir_categoria(ARCH, "Salute/Referti", "2024-05-10", PER_ANNO)
    assert d == ARCH / "Salute/Referti" / "2024"


def test_categoria_per_anno_senza_data_resta_radice():
    assert dir_categoria(ARCH, "Salute/Referti", None, PER_ANNO) == ARCH / "Salute/Referti"
    assert dir_categoria(ARCH, "Salute/Referti", "0000-00-00", PER_ANNO) == ARCH / "Salute/Referti"


def test_categoria_normale_ignora_anno():
    assert dir_categoria(ARCH, "Casa/Utenze/Gas", "2024-05-10", PER_ANNO) == ARCH / "Casa/Utenze/Gas"


def test_strip_anno():
    assert strip_anno("Salute/Referti/2024") == "Salute/Referti"
    assert strip_anno("Salute/Referti") == "Salute/Referti"
    assert strip_anno("Formazione/Corsi/1989") == "Formazione/Corsi"
    # un numero che non e' un anno plausibile resta
    assert strip_anno("Fisco-Tasse/730") == "Fisco-Tasse/730"

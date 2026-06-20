from ocrsys import notify


def test_win_escape_apice_singolo():
    # un nome file con apice singolo non deve rompere/iniettare lo script PS
    assert notify._win("file'; rm -rf .") == "file''; rm -rf ."
    assert "\n" not in notify._win("a\nb")


def test_mac_escape_doppio_apice():
    assert '"' not in notify._mac('titolo "x"')
    assert "\n" not in notify._mac("a\nb")

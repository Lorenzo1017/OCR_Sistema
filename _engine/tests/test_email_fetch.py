from datetime import date
from email.message import EmailMessage

from ocrsys import email_fetch


def test_data_imap_formato():
    assert email_fetch._data_imap(date(2026, 6, 25)) == "25-Jun-2026"
    assert email_fetch._data_imap(date(2026, 1, 1)) == "01-Jan-2026"


def test_nome_sicuro_rimuove_separatori():
    assert email_fetch._nome_sicuro("../../etc/passwd.pdf") == ".._.._etc_passwd.pdf"
    assert email_fetch._nome_sicuro("") == "allegato.pdf"
    assert email_fetch._nome_sicuro("fattura enel.pdf") == "fattura enel.pdf"


def test_nome_libero_evita_collisioni(tmp_path):
    (tmp_path / "doc.pdf").write_text("x")
    assert email_fetch._nome_libero(tmp_path, "doc.pdf").name == "doc_2.pdf"
    assert email_fetch._nome_libero(tmp_path, "nuovo.pdf").name == "nuovo.pdf"


def test_pdf_allegati_estrae_solo_pdf():
    msg = EmailMessage()
    msg["Subject"] = "test"
    msg.set_content("corpo")
    msg.add_attachment(b"%PDF-1.4 ciao", maintype="application",
                       subtype="pdf", filename="bolletta.pdf")
    msg.add_attachment(b"foto", maintype="image", subtype="png",
                       filename="foto.png")
    allegati = email_fetch._pdf_allegati(msg)
    nomi = [n for n, _ in allegati]
    assert nomi == ["bolletta.pdf"]
    assert allegati[0][1] == b"%PDF-1.4 ciao"


def test_scarica_no_op_senza_config(tmp_path, monkeypatch):
    # senza file di configurazione la funzione non fa nulla e ritorna 0
    monkeypatch.setattr(email_fetch.config, "EMAIL_CONFIG", tmp_path / "manca.yaml")
    assert email_fetch.scarica() == 0

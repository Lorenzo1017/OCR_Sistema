"""Bot Telegram per cercare nell'archivio dal telefono. Usa SOLO long-polling in
uscita: nessuna porta aperta sul Mac. Risponde solo alle chat autorizzate.

Setup:
  1. Su Telegram: @BotFather -> /newbot -> ottieni il token
  2. Crea _Sistema/.telegram.yaml (chmod 600):
        token: "123456:ABC-..."
        chat_id: []            # vuoto: scrivi /start al bot e ti dira' il tuo id
  3. Metti il tuo id in chat_id, riavvia (ocr-telegram o LaunchAgent)

Uso: ocr-telegram
"""
import json
import mimetypes
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, telegram
from ocrsys.db import Database


def _api(token: str, metodo: str, params: dict, timeout: int = 35):
    url = f"https://api.telegram.org/bot{token}/{metodo}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _invia_documento(token: str, chat_id, percorso: Path):
    """sendDocument via multipart/form-data (senza dipendenze esterne)."""
    conf = uuid.uuid4().hex
    ctype = mimetypes.guess_type(percorso.name)[0] or "application/octet-stream"
    corpo = bytearray()
    def campo(nome, valore):
        corpo.extend(f"--{conf}\r\nContent-Disposition: form-data; "
                     f'name="{nome}"\r\n\r\n{valore}\r\n'.encode())
    campo("chat_id", str(chat_id))
    corpo.extend(f"--{conf}\r\nContent-Disposition: form-data; "
                 f'name="document"; filename="{percorso.name}"\r\n'
                 f"Content-Type: {ctype}\r\n\r\n".encode())
    corpo.extend(percorso.read_bytes())
    corpo.extend(f"\r\n--{conf}--\r\n".encode())
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendDocument", data=bytes(corpo),
        headers={"Content-Type": f"multipart/form-data; boundary={conf}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _messaggio(token, chat_id, testo):
    try:
        _api(token, "sendMessage", {"chat_id": chat_id, "text": testo,
                                    "parse_mode": "Markdown"})
    except Exception:
        # se il Markdown fa storie, riprova in testo semplice
        try:
            _api(token, "sendMessage", {"chat_id": chat_id, "text": testo})
        except Exception:
            pass


def _gestisci(token, cfg, msg):
    chat_id = msg["chat"]["id"]
    testo = msg.get("text", "")
    if not telegram.autorizzato(chat_id, cfg):
        _messaggio(token, chat_id,
                   f"⛔ Non autorizzato.\nIl tuo chat_id è: `{chat_id}`\n"
                   "Aggiungilo a _Sistema/.telegram.yaml (chat_id) e riavvia il bot.")
        return
    db = Database(config.DB_PATH)
    try:
        risposta, pdf = telegram.risposta(db, testo)
        _messaggio(token, chat_id, risposta)
        for rel in pdf:
            p = config.BASE / rel
            if p.exists():
                try:
                    _invia_documento(token, chat_id, p)
                except Exception:
                    _messaggio(token, chat_id, f"(non riesco a inviare {p.name})")
    finally:
        db.close()


def main():
    cfg = telegram.leggi_config()
    token = cfg.get("token", "")
    if not token:
        print("Manca il token. Crea _Sistema/.telegram.yaml "
              "(vedi .telegram.yaml.esempio).")
        return
    print("Bot Telegram avviato (long-polling). Ctrl-C per fermare.")
    offset = 0
    while True:
        try:
            res = _api(token, "getUpdates",
                       {"offset": offset, "timeout": 30}, timeout=40)
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if msg and "chat" in msg:
                    _gestisci(token, cfg, msg)
        except Exception as e:
            print(f"errore polling: {str(e)[:60]}")
            time.sleep(5)


if __name__ == "__main__":
    main()

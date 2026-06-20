import csv
import hashlib
import shutil
from pathlib import Path

from . import config, preflight, ollama_mgr
from .locking import SingleInstanceLock, AlreadyRunning
from .notify import notify
from .pipeline import build_default_context, process_file


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:                       # a blocchi: no OOM su PDF grandi
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _chiave_errore(f: Path) -> str:
    """Chiave per il conteggio errori: sha del contenuto; se il file non e'
    leggibile, ripiega sul nome (cosi' la quarantena scatta comunque)."""
    try:
        return _sha256(f)
    except Exception:
        return "name:" + hashlib.sha256(f.name.encode("utf-8", "replace")).hexdigest()


def _quarantena(f: Path):
    config.DA_SMISTARE_ERRORI.mkdir(parents=True, exist_ok=True)
    dest = config.DA_SMISTARE_ERRORI / f.name
    i = 2
    while dest.exists():
        dest = config.DA_SMISTARE_ERRORI / f"{f.stem}_v{i}{f.suffix}"
        i += 1
    shutil.move(str(f), str(dest))


def _process_all(ctx, files, stampa=True) -> str:
    ok = skip = dasmistare = errori = 0
    for i, f in enumerate(files, 1):
        if stampa:
            print(f"[{i}/{len(files)}] {f.name} ... ", end="", flush=True)
        try:
            status = process_file(f, ctx)
            if status == "ok":
                ok += 1; _say(stampa, "OK")
            elif status == "skip":
                skip += 1; _say(stampa, "gia fatto (duplicato), rimuovo da inbox")
            else:
                dasmistare += 1; _say(stampa, "-> _DaSmistare")
            f.unlink()
        except Exception as e:
            errori += 1
            with config.LOG_ERRORI.open("a", newline="", encoding="utf-8") as lf:
                csv.writer(lf).writerow([f.name, str(e)])
            try:
                tentativi = ctx.db.record_error(_chiave_errore(f), f.name, str(e))
            except Exception:
                tentativi = 0
            if tentativi >= config.MAX_TENTATIVI:
                _quarantena(f)
                _say(stampa, f"ERRORE (tentativo {tentativi}) -> quarantena: {e}")
            else:
                _say(stampa, f"ERRORE (tentativo {tentativi}/"
                             f"{config.MAX_TENTATIVI}), riprovo dopo: {e}")
    return f"OK:{ok}  DaSmistare:{dasmistare}  Saltati:{skip}  Errori:{errori}"


def _say(stampa, msg):
    if stampa:
        print(msg)


def run_once(stampa=True, notifiche=True) -> str:
    """Un giro completo: preflight -> lock -> (se inbox non vuota) avvia Ollama,
    notifica, processa, scarica modello, notifica esito. Ritorna un riepilogo.
    Sicuro da chiamare ripetutamente (idempotente, lock unico)."""
    problemi = preflight.check()
    if problemi:
        msg = "Ambiente non pronto: " + " | ".join(problemi)
        if stampa:
            print(msg)
        if notifiche:
            notify("OCR Sistema — setup incompleto", problemi[0])
        return msg

    try:
        with SingleInstanceLock(config.LOCK_PATH):
            files = sorted(
                p for p in config.INBOX.iterdir()
                if p.suffix.lower() in config.INPUT_EXTS
            )
            if not files:
                if stampa:
                    print("Inbox vuota. Metti i documenti in:", config.INBOX)
                return "inbox vuota"

            if notifiche:
                notify("OCR Sistema",
                       f"Pipeline avviata: elaboro {len(files)} documenti…")
            if stampa:
                print(f"Trovati {len(files)} documenti. Inizio...\n")

            proc = ollama_mgr.ensure()
            # se Ollama non e' salito, NON processare: i file finirebbero tutti
            # in errore e poi in quarantena pur essendo validi.
            if not ollama_mgr.is_up():
                ollama_mgr.stop_server(proc)
                msg = "Ollama non disponibile: riprovo al prossimo giro."
                if stampa:
                    print(msg)
                if notifiche:
                    notify("OCR Sistema", msg)
                return msg

            ctx = build_default_context()
            try:
                riepilogo = _process_all(ctx, files, stampa=stampa)
            finally:
                ctx.db.close()                # chiude la connessione SQLite
                ollama_mgr.stop_model()       # libera RAM modello
                ollama_mgr.stop_server(proc)  # ferma server se avviato da noi

            if stampa:
                print(f"\nFatto. {riepilogo}")
            if notifiche:
                notify("OCR Sistema — fatto", riepilogo)
            return riepilogo

    except AlreadyRunning:
        if stampa:
            print("Un altro processo OCR e' gia' in corso. Esco.")
        return "gia in corso"

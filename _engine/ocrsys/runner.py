import csv
import hashlib
import shutil
from pathlib import Path

from . import config, preflight, ollama_mgr
from .dates import normalize_date
from .locking import SingleInstanceLock, AlreadyRunning
from .notify import notify
from .pipeline import build_default_context, process_file, plan_file


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


def _conferma_interattiva(nome, meta, data):
    """Mostra la classificazione proposta e chiede conferma/modifica via stdin."""
    print(f"\n--- {nome} ---")
    print(f"  data:      {data or '—'}")
    print(f"  mittente:  {meta.get('mittente','')}")
    print(f"  tipo:      {meta.get('tipo','')}")
    print(f"  dettaglio: {meta.get('dettaglio','')}")
    print(f"  categoria: {meta.get('categoria','') or '(incerto)'}"
          f"{'' if meta.get('valido') else '   [incerto -> _DaSmistare]'}")
    scelta = input("  [Invio]=accetta  [e]=modifica  [s]=_DaSmistare : ").strip().lower()
    meta = dict(meta)
    if scelta == "s":
        meta["valido"] = False
        return meta, data
    if scelta == "e":
        def chiedi(campo, attuale):
            v = input(f"    {campo} [{attuale}]: ").strip()
            return v if v else attuale
        meta["mittente"] = chiedi("mittente", meta.get("mittente", ""))
        meta["tipo"] = chiedi("tipo", meta.get("tipo", ""))
        meta["dettaglio"] = chiedi("dettaglio", meta.get("dettaglio", ""))
        nd = input(f"    data AAAA-MM-GG [{data or ''}]: ").strip()
        if nd:
            data = normalize_date(nd) or data
        meta["categoria"] = chiedi("categoria", meta.get("categoria", ""))
        meta["valido"] = True   # se la categoria non e' valida, finira' comunque in _DaSmistare
        return meta, data
    return meta, data   # Invio = accetta com'è


def _plan_all(ctx, files, conferma=None) -> str:
    """DRY-RUN: mostra cosa farebbe senza toccare nulla."""
    ok = skip = dasmistare = errori = 0
    for i, f in enumerate(files, 1):
        try:
            r = plan_file(f, ctx, conferma)
            if r["status"] == "skip":
                skip += 1
                print(f"[{i}/{len(files)}] {f.name}  ->  (gia' processato)")
            else:
                ok += (r["status"] == "ok")
                dasmistare += (r["status"] == "dasmistare")
                print(f"[{i}/{len(files)}] {f.name}\n        ->  {r['dest']}")
        except Exception as e:
            errori += 1
            print(f"[{i}/{len(files)}] {f.name}  ->  ERRORE: {e}")
    return (f"(DRY-RUN, nessun file toccato) OK:{ok}  DaSmistare:{dasmistare}  "
            f"Saltati:{skip}  Errori:{errori}")


def _process_all(ctx, files, stampa=True, conferma=None) -> str:
    ok = skip = dasmistare = errori = 0
    for i, f in enumerate(files, 1):
        if stampa:
            print(f"[{i}/{len(files)}] {f.name} ... ", end="", flush=True)
        try:
            status = process_file(f, ctx, conferma)
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


def run_once(stampa=True, notifiche=True, dry_run=False, interattivo=False) -> str:
    """Un giro completo: preflight -> lock -> (se inbox non vuota) avvia Ollama,
    notifica, processa, scarica modello, notifica esito. Ritorna un riepilogo.
    Sicuro da chiamare ripetutamente (idempotente, lock unico).
    dry_run: mostra solo cosa farebbe. interattivo: chiede conferma per file."""
    conferma = _conferma_interattiva if interattivo else None
    config.ensure_dirs()   # crea le cartelle dati se mancano (clone fresco)
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
            # rglob: trova i documenti anche dentro eventuali sottocartelle
            # (l'utente puo' organizzare le scansioni in cartelle dentro inbox).
            files = sorted(
                p for p in config.INBOX.rglob("*")
                if p.is_file() and p.suffix.lower() in config.INPUT_EXTS
            )
            if not files:
                if stampa:
                    print("Inbox vuota. Metti i documenti in:", config.INBOX)
                return "inbox vuota"

            if notifiche and not dry_run:
                notify("OCR Sistema",
                       f"Pipeline avviata: elaboro {len(files)} documenti…")
            if stampa:
                modo = " (DRY-RUN)" if dry_run else ""
                print(f"Trovati {len(files)} documenti{modo}. Inizio...\n")

            proc = ollama_mgr.ensure()
            # serve l'OCR+classificazione anche in dry-run, quindi Ollama deve
            # essere su; se non sale, NON processare (file validi finirebbero
            # in quarantena).
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
                if dry_run:
                    riepilogo = _plan_all(ctx, files, conferma=conferma)
                else:
                    riepilogo = _process_all(ctx, files, stampa=stampa,
                                             conferma=conferma)
            finally:
                ctx.db.close()                # chiude la connessione SQLite
                ollama_mgr.stop_model()       # libera RAM modello
                ollama_mgr.stop_server(proc)  # ferma server se avviato da noi

            if stampa:
                print(f"\nFatto. {riepilogo}")
            if notifiche and not dry_run:
                notify("OCR Sistema — fatto", riepilogo)
            return riepilogo

    except AlreadyRunning:
        if stampa:
            print("Un altro processo OCR e' gia' in corso. Esco.")
        return "gia in corso"

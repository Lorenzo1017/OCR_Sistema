import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

from . import config

_WIN = sys.platform.startswith("win")


def is_up() -> bool:
    try:
        urllib.request.urlopen(config.OLLAMA_TAGS_URL, timeout=2)
        return True
    except OSError:
        return False


def ensure(timeout: int = 60):
    """Avvia 'ollama serve' se non gia' attivo. Ritorna il processo avviato
    (da fermare a fine batch) oppure None se era gia' su (lo lasciamo stare:
    puo' servire ad altri progetti). NB: chi chiama deve poi verificare is_up()
    e abortire se False (Ollama non e' salito)."""
    if is_up():
        return None
    if not shutil.which("ollama"):
        return None
    # gruppo di processi separato -> possiamo uccidere anche i figli (runner del
    # modello) a fine batch, senza lasciare processi orfani.
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if _WIN:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(["ollama", "serve"], **kwargs)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_up():
            break
        time.sleep(1)
    return proc


def restart(timeout: int = 40) -> bool:
    """Riavvia Ollama da zero (kill totale + serve). Serve quando il model
    runner crasha a meta' run (bug Metal 'Reentrancy avoided' / HTTP 500).
    Ritorna True se torna su e RISPONDE a una generazione."""
    if not shutil.which("ollama"):
        return False
    if _WIN:
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"],
                       check=False, capture_output=True)
    else:
        subprocess.run(["pkill", "-9", "-f", "ollama"],
                       check=False, capture_output=True)
    time.sleep(2)
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if _WIN:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(["ollama", "serve"], **kwargs)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_up():
            try:                       # serve up != modello ok: verifica generi
                payload = json.dumps({
                    "model": config.OLLAMA_MODEL, "prompt": "ok",
                    "stream": False, "keep_alive": config.OLLAMA_KEEP_ALIVE,
                }).encode()
                req = urllib.request.Request(
                    config.OLLAMA_URL, data=payload,
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    if not json.loads(r.read()).get("error"):
                        return True
            except OSError:
                pass
        time.sleep(2)
    return False


def stop_modello(nome: str):
    """Scarica dalla RAM un modello specifico (per nome)."""
    if nome and shutil.which("ollama"):
        subprocess.run(["ollama", "stop", nome],
                       check=False, capture_output=True)


def stop_model():
    """Scarica il modello text dalla RAM (~5GB liberati) -> Ollama a riposo."""
    stop_modello(config.OLLAMA_MODEL)


def stop_server(proc):
    """Ferma il server SOLO se l'abbiamo avviato noi (proc != None),
    uccidendo l'intero gruppo di processi (server + figli)."""
    if proc is None:
        return
    try:
        if _WIN:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                proc.wait(timeout=8)
            except Exception:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                               check=False, capture_output=True)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            try:
                proc.wait(timeout=8)
            except Exception:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

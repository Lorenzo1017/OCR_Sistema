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


def stop_model():
    """Scarica il modello dalla RAM (~5GB liberati) -> Ollama a riposo."""
    if shutil.which("ollama"):
        subprocess.run(["ollama", "stop", config.OLLAMA_MODEL],
                       check=False, capture_output=True)


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

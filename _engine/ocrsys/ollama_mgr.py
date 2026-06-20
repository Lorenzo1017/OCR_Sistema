import shutil
import subprocess
import time
import urllib.request

from . import config


def is_up() -> bool:
    try:
        urllib.request.urlopen(config.OLLAMA_TAGS_URL, timeout=2)
        return True
    except OSError:
        return False


def ensure(timeout: int = 60):
    """Avvia 'ollama serve' se non gia' attivo. Ritorna il processo avviato
    (da fermare a fine batch) oppure None se Ollama era gia' su (lo lasciamo
    stare: potrebbe servire ad altri progetti)."""
    if is_up():
        return None
    if not shutil.which("ollama"):
        return None
    proc = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
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
    """Ferma il server SOLO se l'abbiamo avviato noi (proc != None)."""
    if proc is not None:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

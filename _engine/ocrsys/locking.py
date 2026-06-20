from pathlib import Path
from filelock import FileLock, Timeout


class AlreadyRunning(Exception):
    """Un altro processo OCR detiene gia' il lock."""


class SingleInstanceLock:
    """Lock esclusivo cross-platform (Windows/Linux/macOS) via 'filelock'.
    Si rilascia all'uscita dal contesto. Usato sia dall'avvio manuale sia dal
    watcher -> mutua esclusione su un unico file."""

    def __init__(self, path: Path):
        # filelock gestisce da solo il file di lock; timeout=0 = non bloccante
        self._lock = FileLock(str(path), timeout=0)

    def __enter__(self):
        try:
            self._lock.acquire()
        except Timeout:
            raise AlreadyRunning(str(self._lock.lock_file))
        return self

    def __exit__(self, *exc):
        self._lock.release()
        return False

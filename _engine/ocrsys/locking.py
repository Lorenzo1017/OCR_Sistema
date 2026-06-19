import fcntl
from pathlib import Path


class AlreadyRunning(Exception):
    """Un altro processo OCR detiene gia' il lock."""


class SingleInstanceLock:
    """Lock esclusivo via fcntl.flock. Si rilascia da solo alla morte del
    processo (niente lock stantii). Usato sia da ocr_processa (manuale) sia
    dal watcher automatico -> mutua esclusione su un unico file."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._fd = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.path, "w")
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._fd.close()
            self._fd = None
            raise AlreadyRunning(str(self.path))
        return self

    def __exit__(self, *exc):
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None
        return False

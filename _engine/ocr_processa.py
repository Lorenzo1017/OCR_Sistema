import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys.runner import run_once


def main():
    # Un giro singolo (manuale). Gestisce da solo Ollama, lock, notifiche.
    run_once(stampa=True, notifiche=True)


if __name__ == "__main__":
    main()

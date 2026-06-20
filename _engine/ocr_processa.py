import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys.runner import run_once

USO = """Uso: ocr-processa [opzioni]
  --dry-run        mostra cosa farebbe senza spostare/rinominare nulla
  --interactive    chiede conferma (accetta/modifica/_DaSmistare) per ogni file
  -h, --help       questo aiuto"""


def main():
    args = set(sys.argv[1:])
    if args & {"-h", "--help"}:
        print(USO)
        return
    dry_run = "--dry-run" in args
    interattivo = ("--interactive" in args) or ("-i" in args)
    run_once(stampa=True, notifiche=True, dry_run=dry_run, interattivo=interattivo)


if __name__ == "__main__":
    main()

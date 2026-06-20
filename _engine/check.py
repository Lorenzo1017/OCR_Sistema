"""Diagnostica OCR_Sistema: verifica hardware e dipendenze, e mostra i comandi
per installare cio' che manca. Uso: python check.py"""
import platform
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocrsys import config, hardware, preflight

# Comandi di installazione per ogni componente, per sistema operativo.
INSTALL = {
    "Darwin": {
        "tesseract": "brew install tesseract tesseract-lang",
        "ocrmypdf": "brew install ocrmypdf",
        "ollama": "brew install ollama   (oppure https://ollama.com/download)",
        "modello": "ollama pull qwen2.5:7b",
    },
    "Linux": {
        "tesseract": "sudo apt install -y tesseract-ocr tesseract-ocr-ita",
        "ocrmypdf": "sudo apt install -y ocrmypdf",
        "ollama": "curl -fsSL https://ollama.com/install.sh | sh",
        "modello": "ollama pull qwen2.5:7b",
    },
    "Windows": {
        "tesseract": "https://github.com/UB-Mannheim/tesseract/wiki (lingua 'ita')",
        "ocrmypdf": "pip install ocrmypdf   (richiede Ghostscript)",
        "ollama": "https://ollama.com/download/windows",
        "modello": "ollama pull qwen2.5:7b",
    },
}


def main():
    so = platform.system()
    inst = INSTALL.get(so, INSTALL["Linux"])
    print("=" * 56)
    print(" OCR_Sistema — diagnostica")
    print("=" * 56)

    # --- Hardware ---
    rep = hardware.report(config.BASE)
    ram = rep["ram_gb"]
    disk = rep["disk_free_gb"]
    print(f"\nHardware ({rep['os']}):")
    print(f"  CPU core   : {rep['cpu']}")
    print(f"  RAM        : {ram:.0f} GB" if ram else "  RAM        : n/d")
    print(f"  Disco libero: {disk:.0f} GB" if disk else "  Disco libero: n/d")
    problemi_hw, avvisi_hw = hardware.valuta(rep)
    for p in problemi_hw:
        print(f"  [!] {p}")
    for a in avvisi_hw:
        print(f"  [~] {a}")
    if not problemi_hw and not avvisi_hw:
        print("  [OK] hardware adeguato.")

    # --- Dipendenze software ---
    print("\nComponenti software:")
    mancanti = []
    for tool in ("tesseract", "ocrmypdf", "ollama"):
        ok = shutil.which(tool) is not None
        print(f"  {'[OK]' if ok else '[!] '} {tool}")
        if not ok:
            mancanti.append(tool)
    if mancanti:
        print("\nComandi per installare cio' che manca:")
        for t in mancanti:
            print(f"  {t:10s}: {inst[t]}")
        print(f"  {'modello':10s}: {inst['modello']}")

    # --- Esito ---
    print("\n" + "-" * 56)
    if problemi_hw:
        print("ESITO: hardware sotto i minimi (potrebbe non funzionare bene).")
    elif mancanti:
        print("ESITO: mancano componenti. Installa con i comandi sopra,")
        print("       oppure lancia il setup automatico:")
        print("       macOS/Linux: bash _engine/setup.sh")
        print("       Windows:     powershell -File _engine\\setup.ps1")
    else:
        print("ESITO: tutto pronto. Metti i documenti in:", config.INBOX)
    print("-" * 56)


if __name__ == "__main__":
    main()

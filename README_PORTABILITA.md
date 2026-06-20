# 🌍 OCR_Sistema — App portabile (macOS · Linux · Windows)

Questa cartella **è l'applicazione**. Puoi spostarla, copiarla o incollarla dove
vuoi (altra cartella, chiavetta USB, altro computer). Il codice non ha percorsi
fissi: si adatta a dove si trova la cartella.

## Cosa è portabile e cosa no

| Elemento | Portabile copia-incolla? |
|---|---|
| Codice (`_engine/`), `categorie.yaml`, documenti (`inbox/`, `archivio/`…) | ✅ Sì, ovunque e su qualsiasi OS |
| Ambiente Python (`_engine/.venv/`) | ❌ Specifico per OS → si **ricrea** col setup |
| Programmi esterni (Tesseract, OCRmyPDF, Ollama) | ❌ Si **installano** una volta per OS |

In pratica: **copi la cartella** → su un nuovo computer **lanci il setup** del suo
sistema operativo (ricrea l'ambiente e installa l'avvio automatico). Fatto.

## Installazione per sistema operativo

### 🍎 macOS / 🐧 Linux
```bash
cd /percorso/della/cartella/OCR_Sistema
bash _engine/setup.sh
```
Installa i programmi (su macOS via Homebrew), crea l'ambiente Python, scarica il
modello e configura l'avvio automatico (LaunchAgent su macOS, systemd su Linux).

### 🪟 Windows
1. Installa una volta: **Tesseract** (con lingua *ita*), **Ghostscript**,
   **OCRmyPDF**, **Ollama** (link mostrati dallo script).
2. In PowerShell, nella cartella:
   ```powershell
   powershell -ExecutionPolicy Bypass -File _engine\setup.ps1
   ```
   Crea l'ambiente, scarica il modello e registra l'avvio automatico (Task Scheduler).

## Come funziona (uguale su tutti gli OS)

- Un **watcher** (`watch.py`) controlla `inbox/` ogni 15 minuti.
- Se trova documenti: avvia Ollama, fa OCR, classifica, rinomina, smista in
  `archivio/`, poi **scarica il modello e ferma Ollama** (torna a riposo).
- Ricevi una **notifica** all'avvio e a fine lavoro (notifica nativa di ogni OS).
- I documenti incerti finiscono in `_DaSmistare/`; gli originali sono salvati in
  `originali/`.

## Comandi manuali (opzionali)

| Azione | macOS/Linux | Windows |
|---|---|---|
| Processa subito | `ocr-processa` | `_engine\.venv\Scripts\python _engine\ocr_processa.py` |
| Cerca un documento | `ocr-cerca "parole"` | `…\python _engine\ocr_cerca.py "parole"` |
| Avvia il watcher a mano | `_engine/.venv/bin/python _engine/watch.py` | `…\python _engine\watch.py` |

## Spostare la cartella (stesso computer)
Spostala pure. Poi ri-lancia il setup del tuo OS **solo** per aggiornare l'avvio
automatico ai nuovi percorsi (non riscarica nulla se già presente). In alternativa
puoi forzare la posizione dei dati con la variabile d'ambiente
`OCR_SISTEMA_HOME`.

## Requisiti
- **Python 3.9+**
- **Tesseract** (con dati lingua *ita*), **OCRmyPDF**, **Ollama** + modello
  `qwen2.5:7b` (~5GB).
- ~16GB RAM consigliati (il modello usa ~5GB solo durante l'elaborazione).

## Problemi comuni
- *"Ambiente non pronto: manca …"* → manca un programma: installalo (vedi sopra).
- *Niente notifiche* → la prima volta consenti le notifiche nelle impostazioni
  dell'OS (su Linux serve `notify-send`).
- *Non parte da solo* → riavvia il computer o ri-lancia il setup.
- I test: `cd _engine && .venv/bin/python -m pytest tests/ -q`.

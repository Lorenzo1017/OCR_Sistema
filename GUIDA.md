# 📂 OCR_Sistema — Guida d'uso

Sistema che prende i tuoi documenti scansionati, li legge (OCR), li rinomina con
data e contenuto, e li ordina da solo in cartelle tematiche. **Tutto sul tuo Mac,
niente internet, nessun dato esce.**

---

## A cosa serve

Butti scansioni disordinate in una cartella → ritrovi PDF rinominati e ordinati così:

```
archivio/Casa/Utenze/Gas/2024-03-15_Enel_bolletta_gas.pdf
archivio/Salute/Referti/2023-11-08_OspedaleSanRaffaele_referto_esami.pdf
archivio/Veicoli/Bollo/2024-01-20_RegioneVeneto_bollo_auto.pdf
```

Nome file = `ANNO-MESE-GIORNO_Mittente_Tipo_Dettaglio.pdf`. Ordinabile per data, chiaro a colpo d'occhio.

---

## Le cartelle (cosa c'è dentro OCR_Sistema)

| Cartella | A cosa serve | La tocchi tu? |
|---|---|---|
| **inbox/** | Ci metti le scansioni DA processare | ✅ Sì, ci butti i file |
| **archivio/** | I documenti finiti, rinominati e ordinati | 👀 Solo per leggerli |
| **_DaSmistare/** | Documenti che il sistema non ha capito bene | ✅ Sì, li sistemi a mano |
| **originali/** | Copia di sicurezza degli originali | ❌ Non toccare (backup) |
| **text/** | Testo grezzo (uso interno) | ❌ Ignora |
| **categorie.yaml** | La lista delle cartelle tematiche | ✅ Modifica se vuoi nuovi temi |

---

## Come si usa — AUTOMATICO

Il sistema lavora **da solo**. Ogni **5 minuti** controlla la cartella `inbox/`:
se trova documenti li processa, rinomina e ordina senza che tu faccia niente.
Se la inbox è vuota non fa nulla.

### Il tuo unico compito
1. Trascina PDF o immagini scansionate dentro **`inbox/`** (quanti vuoi).
2. Aspetta. Entro 5 minuti spariscono dalla inbox e finiscono ordinati.
3. Vai a guardare **`archivio/`** (ordinati per tema) e **`_DaSmistare/`** (gli incerti).

Niente Terminale, niente comandi. Metti e dimentica.

### Notifiche
Ricevi una **notifica macOS** quando la pipeline parte ("Pipeline avviata: elaboro
N documenti…") e una a fine lavoro con l'esito ("OK:.. DaSmistare:.. Errori:..").
La **prima volta** macOS potrebbe chiedere il permesso: consentilo
(System Settings → Notifiche). Così sai sempre quando il sistema lavora.

### Ritrovare un documento
Naviga `archivio/` col Finder, oppure cerca per parola dal Terminale:

```bash
ocr-cerca "enel gas"
```

### Forzare subito un giro
```bash
ocr-processa    # processa la inbox ora, senza aspettare i 5 minuti
```

### Accendere / spegnere l'automatico
- **macOS:** `launchctl unload ~/Library/LaunchAgents/com.ocrsistema.watch.plist`
  (e `load` per riattivare).
- **Linux:** `systemctl --user stop ocrsistema` (e `start`).
- **Windows:** disabilita/abilita il task "OCR_Sistema" in Utilità di pianificazione.

L'automatico riparte da solo a ogni accensione del computer.
Per usarlo su **altri sistemi operativi** vedi `README_PORTABILITA.md`.

---

## Cosa succede ai documenti incerti

Se il sistema non è sicuro di data o categoria, **NON inventa**: mette il file in
**`_DaSmistare/`** con nome `0000-00-00_...`. Tu lo apri, lo rinomini/sposti a mano.
Meglio pochi da sistemare che tanti messi nel posto sbagliato.

---

## Aggiungere nuove cartelle tematiche

Apri **`categorie.yaml`** con un editor di testo. Aggiungi un ramo seguendo lo
schema esistente. Esempio, aggiungere "Animali":

```yaml
Animali:
  Veterinario: []
  Documenti: []
```

Salva. Al prossimo `ocr-processa` il sistema userà anche quelle.

---

## Importante / Sicurezza

- ✅ **Originali al sicuro:** ogni scansione viene copiata in `originali/` prima di toccarla.
- ✅ **Reversibile:** ogni rinomina è registrata in `log_rinomine.csv`. Si può annullare.
- ✅ **Offline totale:** nessun documento lascia il Mac.
- ⚠️ **Prima volta:** prova con 5-10 documenti, controlla che nomi e cartelle ti
  piacciano, POI processa il blocco grande.

---

## Se qualcosa non va

- File saltati / errori → guarda `log_errori.csv` (elenco file falliti).
- Vedere cosa ha fatto l'automatico → apri `log_auto.txt`.
- Vuoi rifare un file → rimettilo in `inbox/` (entro 5 min riparte).
- Dubbi → vedi **CHECKLIST.md** nella stessa cartella.

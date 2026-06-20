# 📂 OCR_Sistema — User guide

A system that takes your scanned documents, reads them (OCR), renames them with
date and content, and sorts them by itself into thematic folders. **Everything on
your Mac, no internet, no data leaves.**

---

## What it's for

You drop messy scans into a folder → you get back renamed and sorted PDFs like this:

```
archivio/Casa/Utenze/Gas/2024-03-15_Enel_bolletta_gas.pdf
archivio/Salute/Referti/2023-11-08_OspedaleSanRaffaele_referto_esami.pdf
archivio/Veicoli/Bollo/2024-01-20_RegioneVeneto_bollo_auto.pdf
```

File name = `YYYY-MM-DD_Sender_Type_Detail.pdf`. Sortable by date, clear at a glance.

---

## The folders (what's inside OCR_Sistema)

| Folder | What it's for | Do you touch it? |
|---|---|---|
| **inbox/** | You put the scans TO be processed here | ✅ Yes, you drop files in |
| **archivio/** | The finished documents, renamed and sorted | 👀 Just to read them |
| **_DaSmistare/** | Documents the system didn't understand well | ✅ Yes, you fix them by hand |
| **originali/** | Backup copy of the originals | ❌ Don't touch (backup) |
| **text/** | Raw text (internal use) | ❌ Ignore |
| **categorie.yaml** | The list of thematic folders | ✅ Edit it if you want new themes |

---

## How to use it — AUTOMATIC

The system works **on its own**. Every **15 minutes** it checks the `inbox/` folder:
if it finds documents, it processes, renames and sorts them without you doing anything.
If the inbox is empty it does nothing.

### Your only job
1. Drag scanned PDFs or images into **`inbox/`** (as many as you want).
2. Wait. Within 15 minutes they disappear from the inbox and end up sorted.
3. Go look at **`archivio/`** (sorted by theme) and **`_DaSmistare/`** (the uncertain ones).

No Terminal, no commands. Set it and forget it.

### Notifications
You get a **macOS notification** when the pipeline starts ("Pipeline started: processing
N documents…") and one at the end of the job with the outcome ("OK:.. DaSmistare:.. Errors:..").
The **first time**, macOS may ask for permission: allow it
(System Settings → Notifications). That way you always know when the system is working.

### Finding a document
Browse `archivio/` in Finder, or search by keyword from the Terminal:

```bash
ocr-cerca "enel gas"
```

### Forcing an immediate run
```bash
ocr-processa    # process the inbox now, without waiting the 15 minutes
```

### Turning the automatic mode on / off
- **macOS:** `launchctl unload ~/Library/LaunchAgents/com.ocrsistema.watch.plist`
  (and `load` to re-enable).
- **Linux:** `systemctl --user stop ocrsistema` (and `start`).
- **Windows:** disable/enable the "OCR_Sistema" task in Task Scheduler.

The automatic mode restarts by itself every time you turn the computer on.
To use it on **other operating systems** see `README_PORTABILITA.md`.

---

## What happens to uncertain documents

If the system isn't sure about the date or category, it **does NOT make things up**: it puts the file in
**`_DaSmistare/`** with a name like `0000-00-00_...`. You open it, rename/move it by hand.
Better a few to fix than many put in the wrong place.

---

## Adding new thematic folders

Open **`categorie.yaml`** with a text editor. Add a branch following the
existing schema. Example, adding "Animali":

```yaml
Animali:
  Veterinario: []
  Documenti: []
```

Save. At the next `ocr-processa` the system will use those too.

---

## Important / Safety

- ✅ **Originals safe:** every scan is copied into `originali/` before it's touched.
- ✅ **Reversible:** every rename is recorded in `log_rinomine.csv`. It can be undone.
- ✅ **Fully offline:** no document leaves the Mac.
- ⚠️ **First time:** try with 5-10 documents, check that the names and folders are to
  your liking, THEN process the big batch.

---

## If something goes wrong

- Skipped files / errors → look at `log_errori.csv` (list of failed files).
- See what the automatic mode did → open `log_auto.txt`.
- Want to redo a file → put it back in `inbox/` (it restarts within 15 min).
- Doubts → see **CHECKLIST.md** in the same folder.

# ✅ CHECKLIST — Quick use of OCR_Sistema

A mental printout before processing. Check off from top to bottom.

---

## 🟢 Normal use (AUTOMATIC)

- [ ] 1. I put the files (PDF/images) in the **`inbox/`** folder
- [ ] 2. ...I do nothing else. Within 15 minutes they start on their own.
- [ ] 3. Later I check **`archivio/`** → files sorted into the folders
- [ ] 4. I check **`_DaSmistare/`** → I manually sort out the few uncertain ones

> Want to force a run right away without waiting? Terminal: `ocr-processa`

---

## 🔵 First time (setup, only once)

- [ ] System installed (Tesseract + Ollama + Qwen2.5 + scripts) — done during setup
- [ ] Tested on **5-10 sample documents**
- [ ] Verified: I like the file names
- [ ] Verified: the sorting folders are correct
- [ ] If everything is OK → I can process the big batch

---

## 🟡 If a document ends up in _DaSmistare

- [ ] I open the PDF and read what it is
- [ ] I rename it following the scheme: `YYYY-MM-DD_Sender_Type_Detail.pdf`
- [ ] I move it to the right folder inside `archivio/`

---

## 🟠 Maintenance (every now and then)

- [ ] Want a new category? → I edit **`categorie.yaml`**
- [ ] I check **`log_errori.csv`**: are there failed files to redo?
- [ ] Files to redo → I put them back in `inbox/` and run again

---

## 🔴 Golden rules (don't forget)

- ❌ **DO NOT** delete the `originali/` folder (it's the backup)
- ❌ **DO NOT** edit the files inside `archivio/` by hand unless needed
- ✅ The originals are always recoverable
- ✅ When in doubt → a file in `_DaSmistare/` is better than one put in the wrong place
- ✅ Everything stays on the Mac, no internet

---

## 📞 Useful commands

| I want to... | I type in the Terminal |
|---|---|
| Force a run right away | `ocr-processa` |
| Search for a document | `ocr-cerca "words"` |
| Turn off the automatic mode | `ocr-auto-off` |
| Turn the automatic mode back on | `ocr-auto-on` |
| See what it did on its own | open `log_auto.txt` |
| See the full guide | open `GUIDA.md` |

# ✅ CHECKLIST — Uso rapido OCR_Sistema

Stampa mentale prima di processare. Spunta dall'alto in basso.

---

## 🟢 Uso normale (AUTOMATICO)

- [ ] 1. Metto i file (PDF/immagini) nella cartella **`inbox/`**
- [ ] 2. ...non faccio altro. Entro 5 minuti partono da soli.
- [ ] 3. Più tardi controllo **`archivio/`** → file ordinati nelle cartelle
- [ ] 4. Controllo **`_DaSmistare/`** → sistemo a mano i pochi incerti

> Vuoi forzare subito senza aspettare? Terminale: `ocr-processa`

---

## 🔵 Prima volta (setup, una sola volta)

- [ ] Sistema installato (Tesseract + Ollama + Qwen2.5 + script) — fatto durante il setup
- [ ] Test su **5-10 documenti** campione
- [ ] Verificato: i nomi file mi piacciono
- [ ] Verificato: le cartelle di smistamento sono giuste
- [ ] Se ok → posso processare il blocco grande

---

## 🟡 Se un documento finisce in _DaSmistare

- [ ] Apro il PDF e leggo cos'è
- [ ] Lo rinomino seguendo lo schema: `AAAA-MM-GG_Mittente_Tipo_Dettaglio.pdf`
- [ ] Lo sposto nella cartella giusta dentro `archivio/`

---

## 🟠 Manutenzione (ogni tanto)

- [ ] Voglio una categoria nuova? → modifico **`categorie.yaml`**
- [ ] Controllo **`log_errori.csv`**: ci sono file falliti da rifare?
- [ ] File da rifare → li rimetto in `inbox/` e rilancio

---

## 🔴 Regole d'oro (non dimenticare)

- ❌ **NON** cancellare la cartella `originali/` (è il backup)
- ❌ **NON** modificare i file dentro `archivio/` a mano se non serve
- ✅ Gli originali sono sempre recuperabili
- ✅ Nel dubbio → un file in `_DaSmistare/` è meglio che messo nel posto sbagliato
- ✅ Tutto resta sul Mac, niente internet

---

## 📞 Comandi utili

| Voglio... | Scrivo nel Terminale |
|---|---|
| Forzare subito un giro | `ocr-processa` |
| Cercare un documento | `ocr-cerca "parole"` |
| Spegnere l'automatico | `ocr-auto-off` |
| Riaccendere l'automatico | `ocr-auto-on` |
| Vedere cosa ha fatto da solo | apro `log_auto.txt` |
| Vedere la guida completa | apro `GUIDA.md` |

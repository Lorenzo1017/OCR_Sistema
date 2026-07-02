# Design: taratura categorie + web UI ricerca + esportazioni

Data: 2026-07-02 — Approvato dall'utente (tutte le sezioni).

## 1. Referti per anno

- `impostazioni.yaml` → `categorie_per_anno: [Salute/Referti]` (lista estendibile).
- Pipeline (`_destinazione`): se categoria in lista **e** data valida, la destinazione
  diventa `archivio/<categoria>/<anno>/<nome>.pdf`. Senza data → radice categoria.
- LLM invariato: sceglie solo la categoria; l'anno lo aggiunge il sistema dalla data.
- DB: `categoria` resta `Salute/Referti` (ricerca e statistiche invariate);
  cambia solo `percorso`.
- `verifica_db._indicizza` e `ocr-sposta`: una sottocartella che è un anno a 4
  cifre NON è parte della categoria (strip in deduzione categoria).
- Migrazione one-time (`migra_per_anno.py`): sposta i referti esistenti nelle
  sottocartelle anno + aggiorna `percorso` nel DB. Idempotente.

## 2. Web UI ricerca — porta 8077

- `webapp.py` unico file, Flask, **sola lettura** DB, bind 127.0.0.1:8077.
- Viste: `/` cerca (FTS5, risultati data/mittente/categoria/tags, link PDF),
  `/sfoglia` (albero categorie con conteggi → lista), `/stats` (numeri ocr-stato).
- Download: CSV e ZIP dei risultati di ricerca correnti (riusa modulo export).
- `/pdf/<id>` serve il file dal percorso DB (path-check dentro BASE).
- LaunchAgent `com.ocrsistema.web` (RunAtLoad + KeepAlive), log `log_web.txt`.

## 3. Esportazioni — `ocr-esporta`

- `esporta.py`: sub-comandi
  - `indice` → CSV completo (data, mittente, tipo, dettaglio, categoria, tags, percorso)
  - `categoria "X"` → ZIP dei PDF (incluse sottocartelle anno)
  - `cerca "query"` → ZIP dei match FTS
  - `backup` → ZIP archivio + index.db + categorie.yaml + impostazioni.yaml
- Output in `~/OCR_Sistema/esportazioni/` (gitignorato), nomi con timestamp.

## Ordine, test, error handling

- Ordine: 1 → 3 → 2 (la web riusa le esportazioni). Commit separati.
- Test pytest per: destinazione per anno, strip anno in verifica_db, CSV export,
  zip categoria, filtri percorso webapp. Route web testate con test client Flask.
- Errori: webapp non modifica mai il DB; export su categoria inesistente → messaggio
  chiaro; migrazione salta file mancanti e stampa il riepilogo.

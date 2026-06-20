import sys
sys.path.insert(0, ".")
from ocrsys import config, ollama_mgr
from ocrsys.pipeline import build_default_context, process_file

config.ensure_dirs()
files = [p for p in config.INBOX.rglob("*")
         if p.is_file() and p.suffix.lower() in config.INPUT_EXTS]

# scegli documenti dei tipi che sbagliavano (per path, minuscolo)
def match(p, keys):
    s = str(p).lower()
    return any(k in s for k in keys)

buckets = {
    "catasto":  ["catasto", "visura", "ade", "planimetria"],
    "tributi":  ["tari", "tosap", "consorzio", "ecoambiente", "bonifica"],
    "mutuo":    ["mutuo"],
    "notaio":   ["notaio", "atto", "rogito"],
    "manut":    ["caldaia", "cancello", "collettore", "fattura"],
}
sample, visti = [], set()
for keys in buckets.values():
    n = 0
    for p in files:
        if p in visti:
            continue
        if match(p, keys):
            sample.append(p); visti.add(p); n += 1
            if n >= 2:
                break
sample = sample[:10]
print(f"Campione mirato: {len(sample)} documenti", flush=True)

proc = ollama_mgr.ensure()
if not ollama_mgr.is_up():
    print("Ollama non disponibile."); sys.exit(1)
ctx = build_default_context()
try:
    for i, f in enumerate(sample, 1):
        try:
            st = process_file(f, ctx)
            if st != "skip":
                f.unlink()   # toglie da inbox come fa il run vero
            print(f"[{i}/{len(sample)}] {f.parent.name}/{f.name}  ->  {st}", flush=True)
        except Exception as e:
            print(f"[{i}/{len(sample)}] {f.name}  ERRORE: {e}", flush=True)
finally:
    ctx.db.close(); ollama_mgr.stop_model(); ollama_mgr.stop_server(proc)
print("FINITO", flush=True)

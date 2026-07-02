"""Web UI locale dell'archivio OCR: ricerca full-text, sfoglia per categoria,
statistiche, download CSV/ZIP. SOLA LETTURA sul DB. Solo localhost.

Avvio manuale:  ocr-web        (http://localhost:8077)
Automatico:     LaunchAgent com.ocrsistema.web
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import (Flask, abort, redirect, render_template_string, request,
                   send_file, url_for)

from ocrsys import config, export
from ocrsys.db import Database

PORT = 8077
app = Flask(__name__)


def _db() -> Database:
    return Database(config.DB_PATH)


_BASE_HTML = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archivio OCR</title><style>
 body{font-family:-apple-system,Segoe UI,sans-serif;margin:0;background:#f5f5f4;color:#1c1917}
 header{background:#292524;color:#fafaf9;padding:.7rem 1.2rem;display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap}
 header a{color:#d6d3d1;text-decoration:none;font-weight:600}
 header a:hover,header a.on{color:#fff}
 main{max-width:1000px;margin:1.2rem auto;padding:0 1rem}
 form.cerca{display:flex;gap:.5rem;margin:.8rem 0}
 input[type=text]{flex:1;padding:.55rem .8rem;font-size:1rem;border:1px solid #d6d3d1;border-radius:8px}
 button{padding:.55rem 1rem;border:0;border-radius:8px;background:#292524;color:#fff;font-size:1rem;cursor:pointer}
 table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden}
 th,td{padding:.5rem .7rem;text-align:left;border-bottom:1px solid #e7e5e4;font-size:.92rem}
 th{background:#e7e5e4}
 tr:hover td{background:#fafaf9}
 a.doc{color:#1d4ed8;text-decoration:none}
 .tag{display:inline-block;background:#e7e5e4;border-radius:6px;padding:0 .4rem;margin-right:.2rem;font-size:.8rem}
 .mut{color:#78716c;font-size:.85rem}
 ul.albero{list-style:none;padding-left:1rem}
 ul.albero li{margin:.15rem 0}
 .n{color:#78716c;font-size:.85rem}
 .card{background:#fff;border-radius:8px;padding:.9rem 1.1rem;margin:.6rem 0}
 .kpi{display:inline-block;min-width:140px;margin:.3rem 1rem .3rem 0}
 .kpi b{font-size:1.5rem;display:block}
</style></head><body>
<header><b>📁 Archivio OCR</b>
 <a href="{{ url_for('home') }}" class="{{ 'on' if vista=='cerca' }}">Cerca</a>
 <a href="{{ url_for('sfoglia') }}" class="{{ 'on' if vista=='sfoglia' }}">Sfoglia</a>
 <a href="{{ url_for('stats') }}" class="{{ 'on' if vista=='stats' }}">Statistiche</a>
 <a href="{{ url_for('csv_indice') }}">Scarica indice CSV</a>
</header><main>{{ corpo|safe }}</main></body></html>"""

_RIGA = """<tr><td>{data}</td><td>{mitt}</td><td>{tipo}</td>
<td><a class="mut" href="/sfoglia?cat={cat}">{cat}</a></td>
<td><a class="doc" href="/pdf/{id}" target="_blank">{nome}</a><br>{tags}</td></tr>"""


def _tabella(righe) -> str:
    if not righe:
        return "<p class='mut'>Nessun documento.</p>"
    out = ["<table><tr><th>Data</th><th>Mittente</th><th>Tipo</th>"
           "<th>Categoria</th><th>Documento</th></tr>"]
    for r in righe:
        tags = "".join(f"<span class='tag'>{t}</span>"
                       for t in (r["tags"] or "").split() if t)
        out.append(_RIGA.format(
            id=r["id"], data=r["data_documento"], mitt=r["mittente"],
            tipo=r["tipo"], cat=r["categoria"], nome=r["nome_file"], tags=tags))
    out.append("</table>")
    return "".join(out)


def _pagina(vista, corpo):
    return render_template_string(_BASE_HTML, vista=vista, corpo=corpo)


@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    db = _db()
    try:
        corpo = [f"""<form class="cerca" action="/">
          <input type="text" name="q" value="{q}" placeholder="Cerca nei documenti (es. mutuo 2024, referto sangue)..." autofocus>
          <button>Cerca</button></form>"""]
        if q:
            ris = db.search(q)
            corpo.append(f"<p class='mut'>{len(ris)} risultati per «{q}»"
                         + (f" — <a href='/zip/cerca?q={q}'>scarica ZIP</a>" if ris else "")
                         + "</p>")
            corpo.append(_tabella(ris))
        else:
            ultimi = [dict(r) for r in db.conn.execute(
                "SELECT * FROM documenti ORDER BY id DESC LIMIT 15")]
            corpo.append("<p class='mut'>Ultimi documenti archiviati:</p>")
            corpo.append(_tabella(ultimi))
        return _pagina("cerca", "".join(corpo))
    finally:
        db.close()


@app.route("/sfoglia")
def sfoglia():
    cat = request.args.get("cat", "").strip("/")
    db = _db()
    try:
        if cat:
            righe = [dict(r) for r in db.conn.execute(
                "SELECT * FROM documenti WHERE categoria=? "
                "ORDER BY data_documento DESC", (cat,))]
            corpo = (f"<p><a href='/sfoglia'>&larr; tutte le categorie</a></p>"
                     f"<h2>{cat} <span class='n'>({len(righe)})</span> "
                     f"— <a href='/zip/categoria?cat={cat}'>scarica ZIP</a></h2>"
                     + _tabella(righe))
        else:
            cats = db.conn.execute(
                "SELECT categoria, COUNT(*) n FROM documenti "
                "GROUP BY categoria ORDER BY categoria").fetchall()
            voci = "".join(
                f"<li><a class='doc' href='/sfoglia?cat={c}'>{c}</a> "
                f"<span class='n'>({n})</span></li>" for c, n in cats)
            corpo = f"<h2>Categorie</h2><ul class='albero'>{voci}</ul>"
        return _pagina("sfoglia", corpo)
    finally:
        db.close()


@app.route("/stats")
def stats():
    db = _db()
    try:
        c = db.conn
        tot = c.execute("SELECT COUNT(*) FROM documenti").fetchone()[0]
        nodate = c.execute("SELECT COUNT(*) FROM documenti WHERE "
                           "data_documento IN ('0000-00-00','')").fetchone()[0]
        ncat = c.execute("SELECT COUNT(DISTINCT categoria) FROM documenti").fetchone()[0]
        ds = len([p for p in config.DA_SMISTARE.glob('*')
                  if p.is_file() and p.suffix.lower() in config.INPUT_EXTS])
        top = c.execute("SELECT categoria, COUNT(*) n FROM documenti "
                        "GROUP BY categoria ORDER BY n DESC LIMIT 12").fetchall()
        massimo = top[0][1] if top else 1
        barre = "".join(
            f"<div style='margin:.2rem 0'><span class='mut'>{cat}</span><br>"
            f"<div style='background:#a8a29e;height:14px;border-radius:4px;"
            f"width:{max(3, 100*n//massimo)}%'></div> {n}</div>"
            for cat, n in top)
        corpo = f"""
        <div class="card">
          <span class="kpi"><b>{tot}</b>documenti</span>
          <span class="kpi"><b>{ncat}</b>categorie</span>
          <span class="kpi"><b>{ds}</b>da smistare</span>
          <span class="kpi"><b>{100*nodate//max(tot,1)}%</b>senza data</span>
        </div>
        <div class="card"><h3>Categorie principali</h3>{barre}</div>"""
        return _pagina("stats", corpo)
    finally:
        db.close()


@app.route("/pdf/<int:doc_id>")
def pdf(doc_id):
    db = _db()
    try:
        r = db.conn.execute("SELECT percorso FROM documenti WHERE id=?",
                            (doc_id,)).fetchone()
    finally:
        db.close()
    if not r:
        abort(404)
    p = (config.BASE / r["percorso"]).resolve()
    # difesa path traversal: il file deve stare dentro la cartella dell'app
    if not str(p).startswith(str(config.BASE.resolve()) + os.sep) or not p.exists():
        abort(404)
    return send_file(p)


@app.route("/csv")
def csv_indice():
    db = _db()
    try:
        dest = export.indice_csv(db)
    finally:
        db.close()
    return send_file(dest, as_attachment=True)


@app.route("/zip/categoria")
def zip_cat():
    cat = request.args.get("cat", "")
    db = _db()
    try:
        dest, agg, _ = export.zip_categoria(db, cat)
    finally:
        db.close()
    if dest is None:
        abort(404)
    return send_file(dest, as_attachment=True)


@app.route("/zip/cerca")
def zip_cerca():
    q = request.args.get("q", "")
    db = _db()
    try:
        dest, agg, _ = export.zip_ricerca(db, q)
    finally:
        db.close()
    if dest is None:
        return redirect(url_for("home", q=q))
    return send_file(dest, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)

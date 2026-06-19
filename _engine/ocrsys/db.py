import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documenti (
    id INTEGER PRIMARY KEY,
    nome_file TEXT, percorso TEXT, categoria TEXT,
    data_documento TEXT, mittente TEXT, tipo TEXT,
    testo_completo TEXT, n_pagine INTEGER, confidenza TEXT,
    sha256 TEXT UNIQUE, data_processato TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS documenti_fts USING fts5(
    mittente, tipo, testo_completo, content='documenti', content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS doc_ai AFTER INSERT ON documenti BEGIN
    INSERT INTO documenti_fts(rowid, mittente, tipo, testo_completo)
    VALUES (new.id, new.mittente, new.tipo, new.testo_completo);
END;
"""


class Database:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def already_processed(self, sha256: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM documenti WHERE sha256 = ?", (sha256,)
        )
        return cur.fetchone() is not None

    def insert(self, doc: dict):
        cols = ["nome_file", "percorso", "categoria", "data_documento",
                "mittente", "tipo", "testo_completo", "n_pagine",
                "confidenza", "sha256"]
        placeholders = ", ".join("?" for _ in cols)
        self.conn.execute(
            f"INSERT OR IGNORE INTO documenti ({', '.join(cols)}) "
            f"VALUES ({placeholders})",
            tuple(doc[c] for c in cols),
        )
        self.conn.commit()

    def search(self, query: str) -> list:
        cur = self.conn.execute(
            "SELECT d.* FROM documenti d "
            "JOIN documenti_fts f ON f.rowid = d.id "
            "WHERE documenti_fts MATCH ? ORDER BY d.data_documento DESC",
            (query,),
        )
        return [dict(r) for r in cur.fetchall()]

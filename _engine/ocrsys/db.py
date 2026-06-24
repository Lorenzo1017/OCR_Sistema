import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documenti (
    id INTEGER PRIMARY KEY,
    nome_file TEXT, percorso TEXT, categoria TEXT,
    data_documento TEXT, mittente TEXT, tipo TEXT, tags TEXT DEFAULT '',
    testo_completo TEXT, n_pagine INTEGER, confidenza TEXT,
    sha256 TEXT UNIQUE, data_processato TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS documenti_fts USING fts5(
    mittente, tipo, tags, testo_completo, content='documenti', content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS doc_ai AFTER INSERT ON documenti BEGIN
    INSERT INTO documenti_fts(rowid, mittente, tipo, tags, testo_completo)
    VALUES (new.id, new.mittente, new.tipo, new.tags, new.testo_completo);
END;
CREATE TABLE IF NOT EXISTS errori (
    sha256 TEXT PRIMARY KEY,
    nome TEXT,
    tentativi INTEGER NOT NULL DEFAULT 0,
    ultimo_errore TEXT
);
"""


class Database:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self):
        """Aggiorna DB creati da versioni precedenti: aggiunge la colonna tags
        e la include nell'indice FTS5 (ricostruendolo)."""
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(documenti)")]
        if "tags" not in cols:
            self.conn.execute("ALTER TABLE documenti ADD COLUMN tags TEXT DEFAULT ''")
        fts_cols = [r[1] for r in self.conn.execute("PRAGMA table_info(documenti_fts)")]
        if "tags" not in fts_cols:
            self.conn.executescript("""
                DROP TRIGGER IF EXISTS doc_ai;
                DROP TABLE IF EXISTS documenti_fts;
                CREATE VIRTUAL TABLE documenti_fts USING fts5(
                    mittente, tipo, tags, testo_completo,
                    content='documenti', content_rowid='id');
                INSERT INTO documenti_fts(rowid, mittente, tipo, tags, testo_completo)
                    SELECT id, mittente, tipo, COALESCE(tags,''), testo_completo
                    FROM documenti;
                CREATE TRIGGER doc_ai AFTER INSERT ON documenti BEGIN
                    INSERT INTO documenti_fts(rowid, mittente, tipo, tags, testo_completo)
                    VALUES (new.id, new.mittente, new.tipo, new.tags, new.testo_completo);
                END;
            """)

    def already_processed(self, sha256: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM documenti WHERE sha256 = ?", (sha256,)
        )
        return cur.fetchone() is not None

    def insert(self, doc: dict) -> bool:
        """Ritorna True se inserito, False se gia' presente (sha duplicato)."""
        cols = ["nome_file", "percorso", "categoria", "data_documento",
                "mittente", "tipo", "tags", "testo_completo", "n_pagine",
                "confidenza", "sha256"]
        placeholders = ", ".join("?" for _ in cols)
        cur = self.conn.execute(
            f"INSERT OR IGNORE INTO documenti ({', '.join(cols)}) "
            f"VALUES ({placeholders})",
            tuple(doc.get(c, "") for c in cols),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def record_error(self, sha256: str, nome: str, errore: str) -> int:
        """Registra un fallimento su un file. Ritorna il numero di tentativi
        totali (incrementale)."""
        self.conn.execute(
            "INSERT INTO errori (sha256, nome, tentativi, ultimo_errore) "
            "VALUES (?, ?, 1, ?) "
            "ON CONFLICT(sha256) DO UPDATE SET "
            "tentativi = tentativi + 1, ultimo_errore = excluded.ultimo_errore",
            (sha256, nome, errore),
        )
        self.conn.commit()
        cur = self.conn.execute(
            "SELECT tentativi FROM errori WHERE sha256 = ?", (sha256,)
        )
        return cur.fetchone()[0]

    @staticmethod
    def _fts_query(query: str) -> str:
        """Input utente -> query FTS5 sicura: ogni parola come termine letterale
        fra apici (i caratteri \" * : ( ) - non vengono interpretati come
        sintassi -> niente 'fts5: syntax error')."""
        return " ".join('"' + t.replace('"', '""') + '"' for t in query.split())

    def known_senders(self, limit: int = 300) -> list:
        """Mittenti gia' archiviati, dal piu' frequente. Passati al prompt LLM
        per riusare la grafia esatta ('Enel') invece di inventarne varianti."""
        cur = self.conn.execute(
            "SELECT mittente FROM documenti "
            "WHERE mittente IS NOT NULL AND TRIM(mittente) <> '' "
            "GROUP BY mittente ORDER BY COUNT(*) DESC LIMIT ?",
            (limit,),
        )
        return [r[0] for r in cur.fetchall()]

    def search(self, query: str) -> list:
        match = self._fts_query(query)
        if not match:
            return []
        cur = self.conn.execute(
            "SELECT d.* FROM documenti d "
            "JOIN documenti_fts f ON f.rowid = d.id "
            "WHERE documenti_fts MATCH ? ORDER BY d.data_documento DESC",
            (match,),
        )
        return [dict(r) for r in cur.fetchall()]

    def aggiorna_per_sha(self, sha256: str, **campi):
        """Aggiorna le colonne indicate per il documento con quel sha."""
        if not campi:
            return
        sets = ", ".join(f"{k} = ?" for k in campi)
        self.conn.execute(
            f"UPDATE documenti SET {sets} WHERE sha256 = ?",
            (*campi.values(), sha256))
        self.conn.commit()

    def rebuild_fts(self):
        """Ricostruisce l'indice FTS dai dati attuali (dopo aggiornamenti)."""
        self.conn.executescript("""
            DROP TRIGGER IF EXISTS doc_ai;
            DROP TABLE IF EXISTS documenti_fts;
            CREATE VIRTUAL TABLE documenti_fts USING fts5(
                mittente, tipo, tags, testo_completo,
                content='documenti', content_rowid='id');
            INSERT INTO documenti_fts(rowid, mittente, tipo, tags, testo_completo)
                SELECT id, mittente, tipo, COALESCE(tags,''), testo_completo
                FROM documenti;
            CREATE TRIGGER doc_ai AFTER INSERT ON documenti BEGIN
                INSERT INTO documenti_fts(rowid, mittente, tipo, tags, testo_completo)
                VALUES (new.id, new.mittente, new.tipo, new.tags, new.testo_completo);
            END;
        """)
        self.conn.commit()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

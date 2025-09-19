import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class Storage:
    """SQLite-backed storage with optional FTS5 full-text search.
    Database file: data/docsense.db
    If FTS5 is unavailable, falls back to a plain table and LIKE-based search.
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "data", "docsense.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._fts = False  # default; will be set during init

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT,  -- admin, employee
                    created_at TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    file_hash TEXT UNIQUE,
                    ext TEXT,
                    language TEXT,
                    doc_type TEXT,
                    role TEXT,
                    created_at TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    doc_id INTEGER,
                    quick JSON,
                    llm JSON,
                    compliance JSON,
                    FOREIGN KEY (doc_id) REFERENCES documents(id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER,
                    user_id INTEGER,
                    sent_at TEXT,
                    FOREIGN KEY (doc_id) REFERENCES documents(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                """
            )
            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                        content,
                        filename,
                        doc_type,
                        language
                    );
                    """
                )
                self._fts = True
            except sqlite3.OperationalError:
                # FTS5 not available; use a normal table for fallback search
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS docs_fts (
                        content TEXT,
                        filename TEXT,
                        doc_type TEXT,
                        language TEXT
                    );
                    """
                )
                self._fts = False

    def save_document(
        self,
        filename: str,
        file_hash: str,
        meta: Dict[str, Any],
        quick: Dict[str, Any],
        llm: Optional[Dict[str, Any]],
        compliance: List[Dict[str, Any]],
        fulltext: str,
    ) -> int:
        created_at = datetime.utcnow().isoformat()
        with self._conn() as conn:
            cur = conn.cursor()
            # Upsert-like logic for deduplication by file_hash
            cur.execute(
                "SELECT id FROM documents WHERE file_hash = ?",
                (file_hash,),
            )
            row = cur.fetchone()
            if row:
                doc_id = row[0]
                # Overwrite analyses to keep latest
                cur.execute("DELETE FROM analyses WHERE doc_id = ?", (doc_id,))
            else:
                cur.execute(
                    "INSERT INTO documents(filename, file_hash, ext, language, doc_type, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        os.path.basename(filename),
                        file_hash,
                        meta.get("ext"),
                        meta.get("language"),
                        meta.get("doc_type"),
                        meta.get("suggested_role"),
                        created_at,
                    ),
                )
                doc_id = cur.lastrowid

            cur.execute(
                "INSERT INTO analyses(doc_id, quick, llm, compliance) VALUES (?, ?, ?, ?)",
                (
                    doc_id,
                    json.dumps(quick, ensure_ascii=False),
                    json.dumps(llm, ensure_ascii=False) if llm else None,
                    json.dumps(compliance, ensure_ascii=False),
                ),
            )
            # Index content for search
            cur.execute(
                "INSERT INTO docs_fts(content, filename, doc_type, language) VALUES (?, ?, ?, ?)",
                (
                    fulltext or "",
                    os.path.basename(filename),
                    meta.get("doc_type"),
                    meta.get("language"),
                ),
            )
        return doc_id

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.id, d.filename, d.ext, d.language, d.doc_type, d.role, d.created_at,
                       a.quick, a.llm, a.compliance
                FROM documents d
                JOIN analyses a ON a.doc_id = d.id
                ORDER BY d.id DESC LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r[0],
                    "filename": r[1],
                    "ext": r[2],
                    "language": r[3],
                    "doc_type": r[4],
                    "role": r[5],
                    "created_at": r[6],
                    "quick": json.loads(r[7]) if r[7] else {},
                    "llm": json.loads(r[8]) if r[8] else {},
                    "compliance": json.loads(r[9]) if r[9] else [],
                }
            )
        return out

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not query:
            return []
        with self._conn() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT rowid, filename, doc_type, language, snippet(docs_fts, 0, '[', ']', '…', 10)
                    FROM docs_fts WHERE docs_fts MATCH ? LIMIT ?
                    """,
                    (query, limit),
                )
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                # Fallback LIKE-based search
                like = f"%{query}%"
                cur.execute(
                    """
                    SELECT NULL as rowid, filename, doc_type, language, substr(content, 1, 200)
                    FROM docs_fts WHERE content LIKE ? LIMIT ?
                    """,
                    (like, limit),
                )
                rows = cur.fetchall()
        results: List[Dict[str, Any]] = []
        for r in rows:
            results.append(
                {
                    "rowid": r[0],
                    "filename": r[1],
                    "doc_type": r[2],
                    "language": r[3],
                    "snippet": r[4],
                }
            )
        return results

    def create_user(self, username: str, email: str, password_hash: str, role: str = "employee") -> int:
        created_at = datetime.utcnow().isoformat()
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users(username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, role, created_at),
            )
            return cur.lastrowid

    def authenticate_user(self, username: str, password_hash: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, email, role FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash),
            )
            row = cur.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "email": row[2], "role": row[3]}
            return None

    def get_users(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, username, email, role FROM users")
            rows = cur.fetchall()
            return [{"id": r[0], "username": r[1], "email": r[2], "role": r[3]} for r in rows]

    def save_recipients(self, doc_id: int, user_ids: List[int]):
        sent_at = datetime.utcnow().isoformat()
        with self._conn() as conn:
            cur = conn.cursor()
            for user_id in user_ids:
                cur.execute(
                    "INSERT INTO document_recipients(doc_id, user_id, sent_at) VALUES (?, ?, ?)",
                    (doc_id, user_id, sent_at),
                )

    def get_user_documents(self, user_id: int) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.id, d.filename, d.ext, d.language, d.doc_type, d.role, d.created_at,
                       a.quick, a.llm, a.compliance
                FROM documents d
                JOIN analyses a ON a.doc_id = d.id
                JOIN document_recipients dr ON dr.doc_id = d.id
                WHERE dr.user_id = ?
                ORDER BY d.id DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "id": r[0],
                        "filename": r[1],
                        "ext": r[2],
                        "language": r[3],
                        "doc_type": r[4],
                        "role": r[5],
                        "created_at": r[6],
                        "quick": json.loads(r[7]) if r[7] else {},
                        "llm": json.loads(r[8]) if r[8] else {},
                        "compliance": json.loads(r[9]) if r[9] else [],
                    }
                )
            return out
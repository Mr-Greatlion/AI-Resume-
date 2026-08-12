"""
SQLite store — keeps only the last MAX_RECORDS on disk.
Zero setup. No Postgres needed for v2.
"""
from __future__ import annotations
import json, os, sqlite3
from datetime import datetime
from app_v2.config import DB_PATH, MAX_RECORDS


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                uid          TEXT    NOT NULL UNIQUE,
                filename     TEXT    NOT NULL,
                stored_path  TEXT,
                parsed_json  TEXT    NOT NULL DEFAULT '{}',
                proc_status  TEXT    NOT NULL DEFAULT 'success',
                extract_ms   INTEGER,
                error_msg    TEXT,
                created_at   TEXT    NOT NULL
            )
        """)
        c.commit()


def save_record(uid: str, filename: str, stored_path: str,
                parsed: dict, status: str, ms: int, error: str | None) -> None:
    """Insert and immediately prune so only MAX_RECORDS rows remain."""
    with _conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO records
               (uid,filename,stored_path,parsed_json,proc_status,extract_ms,error_msg,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (uid, filename, stored_path,
             json.dumps(parsed, ensure_ascii=False),
             status, ms, error,
             datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        )
        # get paths of rows that will be purged
        old = c.execute("""
            SELECT stored_path FROM records
            WHERE id NOT IN (SELECT id FROM records ORDER BY id DESC LIMIT ?)
              AND stored_path IS NOT NULL
        """, (MAX_RECORDS,)).fetchall()
        for row in old:
            try:
                if row["stored_path"] and os.path.exists(row["stored_path"]):
                    os.remove(row["stored_path"])
            except Exception:
                pass
        c.execute("""
            DELETE FROM records
            WHERE id NOT IN (SELECT id FROM records ORDER BY id DESC LIMIT ?)
        """, (MAX_RECORDS,))
        c.commit()


def list_records() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_record(uid: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM records WHERE uid=?", (uid,)).fetchone()
    return _row_to_dict(row) if row else None


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["fields"] = json.loads(d.pop("parsed_json", "{}"))
    return d

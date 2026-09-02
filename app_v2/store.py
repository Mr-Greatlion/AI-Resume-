"""
Storage for v2.

Two tables / collections:
  extractions   one row per uploaded resume: the file, raw text, what the AI extracted
  reviews       one row per "Submit for Data Training": what the reviewer confirmed/edited,
                plus a per-field diff (extracted vs reviewed) = training data
  certificates  uploaded certificate files linked to an extraction

Backend is chosen from environment:
  MONGO_URI set            → MongoDB (Atlas / AWS DocumentDB)
  otherwise DATABASE_URL   → SQLAlchemy: sqlite (default) / postgresql / mysql (AWS RDS)
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from app_v2.config import DATABASE_URL, MAX_RECORDS, MONGO_DB, MONGO_URI

log = logging.getLogger("resume_v2.store")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ═════════════════════════════════════════════════════════════════════════════
#  SQL backend (SQLAlchemy Core — works on sqlite, postgres, mysql)
# ═════════════════════════════════════════════════════════════════════════════

class SQLStore:
    backend = "sql"

    def __init__(self, url: str):
        from sqlalchemy import (Column, Integer, MetaData, String, Table, Text, create_engine)
        self.url = url
        if url.startswith("sqlite"):
            path = url.replace("sqlite:///", "")
            if path and path != ":memory:":
                os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
            self.engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
        else:
            self.engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800, future=True)
        md = MetaData()
        self.t_ext = Table(
            "resume_extractions", md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("uid", String(40), nullable=False, unique=True, index=True),
            Column("filename", String(255), nullable=False),
            Column("stored_path", String(500)),
            Column("mime", String(100)),
            Column("size_bytes", Integer),
            Column("extract_method", String(20)),
            Column("proc_status", String(20), nullable=False, default="success"),
            Column("duration_ms", Integer),
            Column("error_msg", Text),
            Column("raw_text", Text),
            Column("extracted_json", Text, nullable=False, default="{}"),
            Column("meta_json", Text, nullable=False, default="{}"),
            Column("review_status", String(20), nullable=False, default="pending"),
            Column("created_at", String(25), nullable=False),
        )
        self.t_rev = Table(
            "resume_reviews", md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("uid", String(40), nullable=False, index=True),
            Column("reviewer", String(120)),
            Column("reviewed_json", Text, nullable=False),
            Column("corrections_json", Text, nullable=False),
            Column("fields_total", Integer),
            Column("fields_changed", Integer),
            Column("accuracy_pct", Integer),
            Column("notes", Text),
            Column("webhook_status", String(60)),
            Column("submitted_at", String(25), nullable=False),
        )
        self.t_cert = Table(
            "resume_certificates", md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("cert_id", String(40), nullable=False, unique=True, index=True),
            Column("uid", String(40), nullable=False, index=True),
            Column("name", String(200)),
            Column("filename", String(255)),
            Column("stored_path", String(500)),
            Column("size_bytes", Integer),
            Column("created_at", String(25), nullable=False),
        )
        md.create_all(self.engine)
        log.info("SQL store ready (%s)", url.split("@")[-1] if "@" in url else url)

    # ── helpers ──
    def _rows(self, stmt) -> list[dict]:
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(stmt)]

    # ── extractions ──
    def save_extraction(self, rec: dict) -> None:
        from sqlalchemy import delete, insert, select
        row = dict(
            uid=rec["uid"], filename=rec["filename"], stored_path=rec.get("stored_path"),
            mime=rec.get("mime"), size_bytes=rec.get("size_bytes"),
            extract_method=rec.get("extract_method"), proc_status=rec.get("proc_status", "success"),
            duration_ms=rec.get("duration_ms"), error_msg=rec.get("error_msg"),
            raw_text=rec.get("raw_text"),
            extracted_json=json.dumps(rec.get("extracted", {}), ensure_ascii=False),
            meta_json=json.dumps(rec.get("meta", {}), ensure_ascii=False),
            review_status="pending", created_at=_now(),
        )
        with self.engine.begin() as c:
            c.execute(insert(self.t_ext).values(**row))
            if MAX_RECORDS > 0:
                keep = [r[0] for r in c.execute(
                    select(self.t_ext.c.id).order_by(self.t_ext.c.id.desc()).limit(MAX_RECORDS))]
                old = c.execute(select(self.t_ext.c.uid, self.t_ext.c.stored_path)
                                .where(self.t_ext.c.id.not_in(keep))).all()
                for uid, path in old:
                    _remove_file(path)
                    c.execute(delete(self.t_rev).where(self.t_rev.c.uid == uid))
                    c.execute(delete(self.t_cert).where(self.t_cert.c.uid == uid))
                c.execute(delete(self.t_ext).where(self.t_ext.c.id.not_in(keep)))

    def get_extraction(self, uid: str) -> dict | None:
        from sqlalchemy import select
        rows = self._rows(select(self.t_ext).where(self.t_ext.c.uid == uid))
        return _ext_row(rows[0]) if rows else None

    def list_extractions(self, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        from sqlalchemy import func, select
        with self.engine.connect() as c:
            total = c.execute(select(func.count()).select_from(self.t_ext)).scalar() or 0
        rows = self._rows(select(self.t_ext).order_by(self.t_ext.c.id.desc()).limit(limit).offset(offset))
        return [_ext_row(r, brief=True) for r in rows], int(total)

    # ── reviews ──
    def save_review(self, rev: dict) -> int:
        from sqlalchemy import insert, update
        with self.engine.begin() as c:
            res = c.execute(insert(self.t_rev).values(
                uid=rev["uid"], reviewer=rev.get("reviewer"),
                reviewed_json=json.dumps(rev["reviewed"], ensure_ascii=False),
                corrections_json=json.dumps(rev["corrections"], ensure_ascii=False),
                fields_total=rev.get("fields_total"), fields_changed=rev.get("fields_changed"),
                accuracy_pct=rev.get("accuracy_pct"), notes=rev.get("notes"),
                webhook_status=rev.get("webhook_status"), submitted_at=_now(),
            ))
            c.execute(update(self.t_ext).where(self.t_ext.c.uid == rev["uid"]).values(review_status="reviewed"))
            pk = res.inserted_primary_key[0] if res.inserted_primary_key else 0
        return int(pk or 0)

    def get_reviews(self, uid: str) -> list[dict]:
        from sqlalchemy import select
        rows = self._rows(select(self.t_rev).where(self.t_rev.c.uid == uid).order_by(self.t_rev.c.id.desc()))
        return [_rev_row(r) for r in rows]

    def iter_training(self, limit: int = 10000) -> list[dict]:
        from sqlalchemy import select
        j = self.t_rev.join(self.t_ext, self.t_rev.c.uid == self.t_ext.c.uid)
        stmt = (select(self.t_rev, self.t_ext.c.filename, self.t_ext.c.raw_text, self.t_ext.c.extracted_json)
                .select_from(j).order_by(self.t_rev.c.id.desc()).limit(limit))
        out = []
        for r in self._rows(stmt):
            d = _rev_row(r)
            d.update(filename=r["filename"], raw_text=r["raw_text"],
                     extracted=json.loads(r["extracted_json"] or "{}"))
            out.append(d)
        return out

    # ── certificates ──
    def save_certificate(self, cert: dict) -> None:
        from sqlalchemy import insert
        with self.engine.begin() as c:
            c.execute(insert(self.t_cert).values(
                cert_id=cert["cert_id"], uid=cert["uid"], name=cert.get("name"),
                filename=cert.get("filename"), stored_path=cert.get("stored_path"),
                size_bytes=cert.get("size_bytes"), created_at=_now()))

    def get_certificate(self, cert_id: str) -> dict | None:
        from sqlalchemy import select
        rows = self._rows(select(self.t_cert).where(self.t_cert.c.cert_id == cert_id))
        return rows[0] if rows else None

    def list_certificates(self, uid: str) -> list[dict]:
        from sqlalchemy import select
        return self._rows(select(self.t_cert).where(self.t_cert.c.uid == uid).order_by(self.t_cert.c.id))

    def stats(self) -> dict:
        from sqlalchemy import func, select
        with self.engine.connect() as c:
            n_ext = c.execute(select(func.count()).select_from(self.t_ext)).scalar() or 0
            n_rev = c.execute(select(func.count()).select_from(self.t_rev)).scalar() or 0
            acc = c.execute(select(func.avg(self.t_rev.c.accuracy_pct))).scalar()
        return {"extractions": int(n_ext), "reviews": int(n_rev),
                "avgAccuracyPct": round(float(acc), 1) if acc is not None else None}

    def ping(self) -> bool:
        from sqlalchemy import text
        try:
            with self.engine.connect() as c:
                c.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            log.error("DB ping failed: %s", exc)
            return False


# ═════════════════════════════════════════════════════════════════════════════
#  Mongo backend
# ═════════════════════════════════════════════════════════════════════════════

class MongoStore:
    backend = "mongo"

    def __init__(self, uri: str, dbname: str):
        from pymongo import ASCENDING, DESCENDING, MongoClient
        self.client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        self.db = self.client[dbname]
        self.ext = self.db["resume_extractions"]
        self.rev = self.db["resume_reviews"]
        self.cert = self.db["resume_certificates"]
        self.ext.create_index([("uid", ASCENDING)], unique=True)
        self.ext.create_index([("created_at", DESCENDING)])
        self.rev.create_index([("uid", ASCENDING)])
        self.cert.create_index([("cert_id", ASCENDING)], unique=True)
        self.cert.create_index([("uid", ASCENDING)])
        log.info("Mongo store ready (db=%s)", dbname)

    @staticmethod
    def _strip(d: dict | None) -> dict | None:
        if d is None:
            return None
        d = dict(d)
        d.pop("_id", None)
        return d

    def save_extraction(self, rec: dict) -> None:
        doc = {k: v for k, v in rec.items()}
        doc["review_status"] = "pending"
        doc["created_at"] = _now()
        self.ext.replace_one({"uid": rec["uid"]}, doc, upsert=True)
        if MAX_RECORDS > 0:
            keep = {d["uid"] for d in self.ext.find({}, {"uid": 1}).sort("created_at", -1).limit(MAX_RECORDS)}
            for d in self.ext.find({"uid": {"$nin": list(keep)}}, {"uid": 1, "stored_path": 1}):
                _remove_file(d.get("stored_path"))
                self.rev.delete_many({"uid": d["uid"]})
                self.cert.delete_many({"uid": d["uid"]})
                self.ext.delete_one({"uid": d["uid"]})

    def get_extraction(self, uid: str) -> dict | None:
        return self._strip(self.ext.find_one({"uid": uid}))

    def list_extractions(self, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        total = self.ext.count_documents({})
        rows = [self._strip(d) for d in self.ext.find({}).sort("created_at", -1).skip(offset).limit(limit)]
        for r in rows:
            r.pop("raw_text", None)
        return rows, int(total)

    def save_review(self, rev: dict) -> int:
        doc = dict(rev)
        doc["submitted_at"] = _now()
        res = self.rev.insert_one(doc)
        self.ext.update_one({"uid": rev["uid"]}, {"$set": {"review_status": "reviewed"}})
        return int(str(res.inserted_id)[-8:], 16)

    def get_reviews(self, uid: str) -> list[dict]:
        return [self._strip(d) for d in self.rev.find({"uid": uid}).sort("submitted_at", -1)]

    def iter_training(self, limit: int = 10000) -> list[dict]:
        out = []
        for r in self.rev.find({}).sort("submitted_at", -1).limit(limit):
            r = self._strip(r)
            e = self.ext.find_one({"uid": r["uid"]}) or {}
            r.update(filename=e.get("filename"), raw_text=e.get("raw_text"), extracted=e.get("extracted", {}))
            out.append(r)
        return out

    def save_certificate(self, cert: dict) -> None:
        doc = dict(cert)
        doc["created_at"] = _now()
        self.cert.replace_one({"cert_id": cert["cert_id"]}, doc, upsert=True)

    def get_certificate(self, cert_id: str) -> dict | None:
        return self._strip(self.cert.find_one({"cert_id": cert_id}))

    def list_certificates(self, uid: str) -> list[dict]:
        return [self._strip(d) for d in self.cert.find({"uid": uid})]

    def stats(self) -> dict:
        n_ext, n_rev = self.ext.count_documents({}), self.rev.count_documents({})
        acc = None
        if n_rev:
            agg = list(self.rev.aggregate([{"$group": {"_id": None, "a": {"$avg": "$accuracy_pct"}}}]))
            acc = round(float(agg[0]["a"]), 1) if agg and agg[0].get("a") is not None else None
        return {"extractions": int(n_ext), "reviews": int(n_rev), "avgAccuracyPct": acc}

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception as exc:
            log.error("Mongo ping failed: %s", exc)
            return False


# ═════════════════════════════════════════════════════════════════════════════
#  shared helpers + factory
# ═════════════════════════════════════════════════════════════════════════════

def _remove_file(path: str | None) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _ext_row(r: dict, brief: bool = False) -> dict:
    d = dict(r)
    d["extracted"] = json.loads(d.pop("extracted_json", "{}") or "{}")
    d["meta"] = json.loads(d.pop("meta_json", "{}") or "{}")
    d.pop("id", None)
    if brief:
        d.pop("raw_text", None)
    return d


def _rev_row(r: dict) -> dict:
    d = dict(r)
    d["reviewed"] = json.loads(d.pop("reviewed_json", "{}") or "{}")
    d["corrections"] = json.loads(d.pop("corrections_json", "{}") or "{}")
    d["review_id"] = d.pop("id", None)
    return d


_store: Any = None


def get_store():
    """Singleton store, created on first use (so import never touches the DB)."""
    global _store
    if _store is None:
        if MONGO_URI:
            _store = MongoStore(MONGO_URI, MONGO_DB)
        else:
            _store = SQLStore(DATABASE_URL)
    return _store


def reset_store() -> None:
    """Testing helper."""
    global _store
    _store = None

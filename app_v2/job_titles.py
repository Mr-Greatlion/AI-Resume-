"""
Job-title dropdown source.

get_job_titles()  → live list from the AVR API (cached JOB_TITLE_TTL seconds),
                    merged with the built-in fallback so the dropdown is never empty.
match_job_title() → fuzzy-map a raw phrase ("Instrumental Technician") to the
                    closest dropdown entry ("Instrumentation Technician").
"""
from __future__ import annotations

import logging
import re
import threading
import time

from app_v2 import constants as C
from app_v2.config import JOB_TITLE_API, JOB_TITLE_TTL

log = logging.getLogger("resume_v2.job_titles")

_lock = threading.Lock()
_cache: dict = {"titles": [], "departments": [], "fetched": 0.0, "live": False}

_SYNONYMS = [
    (r"\binstrumental\b", "instrumentation"),
    (r"\binstrument\b", "instrumentation"),
    (r"\be\s*&\s*i\b|\belectrical\s*(and|&)\s*instrumentation\b", "e&i"),
    (r"\bin[\s\-]?charge\b", "incharge"),
    (r"\bsr\.?\b|\bsenior\b", ""),
    (r"\bjr\.?\b|\bjunior\b", ""),
    (r"\btrainee\b|\bapprentice\b", ""),
    (r"\bmaintenance\s+engineer\b", "mechanical engineer"),
]


def _fetch_live() -> tuple[list[str], list[dict]]:
    import requests
    r = requests.get(JOB_TITLE_API, timeout=6)
    r.raise_for_status()
    data = r.json()
    titles: list[str] = []
    departments: list[dict] = []
    for dept in data.get("data", []) or []:
        d_titles = [j["name"].strip() for j in dept.get("jobTitles", []) or [] if j.get("name")]
        departments.append({"name": dept.get("name", ""), "jobTitles": d_titles})
        titles.extend(d_titles)
    return titles, departments


def get_job_titles(force: bool = False) -> list[str]:
    with _lock:
        fresh = (time.time() - _cache["fetched"]) < JOB_TITLE_TTL
        if _cache["titles"] and fresh and not force:
            return _cache["titles"]
        try:
            live, departments = _fetch_live()
            _cache.update(live=bool(live), departments=departments)
        except Exception as exc:
            log.warning("job-title API unavailable (%s) — using fallback list", exc)
            live = []
            _cache["live"] = False
        merged: list[str] = []
        for t in live + C.JOB_TITLE_FALLBACK:
            if t and t.lower() not in {m.lower() for m in merged}:
                merged.append(t)
        _cache.update(titles=merged, fetched=time.time())
        return merged


def get_departments() -> list[dict]:
    get_job_titles()
    return _cache["departments"]


def job_titles_live() -> bool:
    return bool(_cache["live"])


def _norm(s: str) -> str:
    s = s.lower()
    for pat, rep in _SYNONYMS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"[^a-z&\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match_job_title(raw: str, options: list[str], threshold: int = 78) -> tuple[str, int]:
    """Return (best_option, score 0-100). ('', 0) when nothing is close enough."""
    if not raw or not options:
        return "", 0
    q = _norm(raw)
    if not q:
        return "", 0
    try:
        from rapidfuzz import fuzz
    except ImportError:  # pragma: no cover
        fuzz = None
    best, best_score = "", 0
    for opt in options:
        o = _norm(opt)
        if not o:
            continue
        if o == q:
            return opt, 100
        if fuzz:
            score = int(max(fuzz.token_set_ratio(q, o), fuzz.WRatio(q, o) * 0.9))
            # penalise matches that only share generic words like "engineer"
            q_toks, o_toks = set(q.split()), set(o.split())
            shared = q_toks & o_toks
            if shared and shared <= {"engineer", "technician", "operator", "manager", "executive", "officer"}:
                score = min(score, 60)
        else:
            score = 100 if o in q or q in o else 0
        if score > best_score:
            best, best_score = opt, score
    if best_score >= threshold:
        return best, best_score
    return "", best_score

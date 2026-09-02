"""
v2 extraction layer.

Every field is returned as a descriptor:
    {"value": ..., "status": "extracted" | "low_confidence" | "not_extracted",
     "confidence": 0.0-1.0, "source": "where it came from"}

Strategy per field:
  1. run the v1 extractors from app/ (same code the live v1 API uses)
  2. run v2's own extractors (country-aware phones, job-title → dropdown match,
     experience bucket, education dropdown match, Nigeria/India location lookup)
  3. validate + normalise so every value fits the review form dropdowns

If the v1 package cannot be imported (spaCy missing etc.) v2 silently falls
back to its own extractors — the API never crashes because of v1.
"""
from __future__ import annotations

import logging
import re
import sys
import time
from datetime import date
from typing import Any

from app_v2 import constants as C
from app_v2.config import V1_APP_PATH
from app_v2.job_titles import get_job_titles, match_job_title

log = logging.getLogger("resume_v2.extractor")

EXTRACTED, LOW, MISSING = "extracted", "low_confidence", "not_extracted"


def F(value: Any = "", confidence: float = 0.0, source: str = "") -> dict:
    """Build a field descriptor. Empty value → not_extracted."""
    empty = value in ("", None, [], {}) or (isinstance(value, dict) and not any(value.values()))
    if empty:
        return {"value": value if isinstance(value, (list, dict)) else "", "status": MISSING,
                "confidence": 0.0, "source": source or "none"}
    status = EXTRACTED if confidence >= 0.7 else LOW
    return {"value": value, "status": status, "confidence": round(float(confidence), 2), "source": source}


# ── v1 bridge ────────────────────────────────────────────────────────────────

_v1_cache: dict | None = None


def v1() -> dict:
    """Lazy-import the v1 extractor functions. Returns {} if unavailable."""
    global _v1_cache
    if _v1_cache is not None:
        return _v1_cache
    if V1_APP_PATH and V1_APP_PATH not in sys.path:
        sys.path.insert(0, V1_APP_PATH)
    try:
        from app.extractor import (extract_name, extract_email, extract_phone,  # type: ignore
                                   extract_job_title, detect_pan, detect_aadhaar)
        from app.education_extractor import extract_education  # type: ignore
        from app.experience_calc import calculate_experience  # type: ignore
        from app.address_extractor import extract_address, extract_current_location  # type: ignore
        _v1_cache = dict(name=extract_name, email=extract_email, phone=extract_phone,
                         job=extract_job_title, pan=detect_pan, aadhaar=detect_aadhaar,
                         edu=extract_education, exp=calculate_experience,
                         addr=extract_address, loc=extract_current_location)
        log.info("v1 extractors loaded from %s", V1_APP_PATH)
    except Exception as exc:  # ImportError, OSError (spacy model) ...
        log.warning("v1 extractors unavailable (%s) — using v2 built-in extractors only", exc)
        _v1_cache = {}
    return _v1_cache


def _safe(fn, *args, default=None):
    try:
        return fn(*args) if fn else default
    except Exception as exc:
        log.warning("v1 %s failed: %s", getattr(fn, "__name__", fn), exc)
        return default


# ── text helpers ─────────────────────────────────────────────────────────────

def _lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def _section(text: str, heading_re: str, max_lines: int = 14) -> str:
    """Return the lines that follow a heading like 'Education' until the next heading."""
    lines = _lines(text)
    out: list[str] = []
    started = False
    for ln in lines:
        low = ln.lower().strip(" :-–_*|")
        if not started:
            if re.fullmatch(heading_re, low) or (len(low) < 40 and re.search(heading_re, low)):
                started = True
            continue
        if len(low) < 40 and re.fullmatch(r"(work\s*)?experience|employment.*|skills?|projects?|personal (details|information|profile)|declaration|languages?|hobbies|references?|interests?|objective|summary|certifications?|trainings?|achievements?|profile|contact.*", low):
            break
        out.append(ln)
        if len(out) >= max_lines:
            break
    return "\n".join(out)


ROLE_RE = "|".join(C.ROLE_WORDS)
ROLE_PHRASE = re.compile(
    r"((?:[A-Za-z&/\-\.]+[ \t]+){0,4}(?:" + ROLE_RE + r")s?)\b", re.I)
NAME_BAD = re.compile(
    r"\d|@|resume|curriculum|vitae|profile|summary|objective|address|phone|email|mobile|"
    r"engineer|technician|operator|manager|experience|education|skills|nigeria|india|"
    r"street|road|state|city|contact|\bdob\b|date of birth|father|gender|male|female|nationality", re.I)


# ── country detection ────────────────────────────────────────────────────────

def detect_country(text: str) -> tuple[str, float]:
    low = text.lower()
    score: dict[str, float] = {}

    def add(c: str, w: float):
        score[c] = score.get(c, 0) + w

    for alias, country in C.COUNTRY_ALIASES.items():
        n = len(re.findall(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", low))
        if n:
            add(country, 3.0 * min(n, 4))
    for city, (_state, country) in C.CITY_LOOKUP.items():
        if re.search(r"(?<![a-z])" + re.escape(city) + r"(?![a-z])", low):
            add(country, 2.0)
    for country, states in C.STATES.items():
        for st in states:
            if len(st) > 4 and re.search(r"(?<![a-z])" + re.escape(st.lower()) + r"(?![a-z])", low):
                add(country, 1.5)
    # phone / national hints
    if re.search(r"\+234|\b0[789][01]\d{8}\b", text):
        add("Nigeria", 4)
    if re.search(r"\+91|\b[6-9]\d{9}\b", text):
        add("India", 2)
    if re.search(r"\bnysc\b|\bwaec\b|\bneco\b|\bl\.?g\.?a\b|local government|\bhnd\b|\bond\b|polytechnic", low):
        add("Nigeria", 2)
    if re.search(r"\baadha?ar\b|\bpan\s*(no|card|number)\b|\bpin\s*(code)?\s*[:\-]?\s*\d{6}\b|\btamil\b|\bkerala\b", low):
        add("India", 2)
    if not score:
        return "", 0.0
    best = max(score, key=score.get)
    total = sum(score.values())
    return best, min(1.0, score[best] / max(total, 1)) * (0.6 if score[best] < 3 else 1.0)


# ── name ─────────────────────────────────────────────────────────────────────

def _clean_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z .'\-]", " ", name or "")
    name = re.sub(r"\s+", " ", name).strip(" .-'")
    toks = name.split()
    # drop leading 1–2 letter logo/initial junk when a real name follows ("CI CALISTUS IWUJI")
    while len(toks) > 2 and len(toks[0].strip(".")) <= 2:
        toks = toks[1:]
    toks = [t for t in toks if t.lower() not in ("mr", "mrs", "ms", "dr", "er", "sri", "smt", "shri")]
    return " ".join(t.capitalize() if not re.fullmatch(r"[A-Za-z]\.?", t) else t.upper() for t in toks)


def _name_from_header(text: str) -> tuple[str, float]:
    for ln in _lines(text)[:8]:
        cand = re.sub(r"\s*[|•·].*$", "", ln).strip()
        if NAME_BAD.search(cand):
            continue
        cleaned = _clean_name(cand)
        toks = cleaned.split()
        if 1 <= len(toks) <= 4 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'\-]*", t) for t in toks):
            if len(toks) == 1 and len(toks[0]) < 4:
                continue
            return cleaned, 0.85 if len(toks) >= 2 else 0.6
    return "", 0.0


def _name_from_email(emails: list[str]) -> str:
    for e in emails:
        user = re.sub(r"\d+", "", e.split("@")[0]).replace(".", " ").replace("_", " ")
        parts = [p for p in user.split() if len(p) > 1 and p.isalpha()]
        if 1 <= len(parts) <= 3:
            return " ".join(p.capitalize() for p in parts)
    return ""


def extract_name(text: str, emails: list[str]) -> dict:
    v = v1()
    cands: list[tuple[str, float, str]] = []
    v1_name = _clean_name(_safe(v.get("name"), text, default="") or "")
    if v1_name and not NAME_BAD.search(v1_name) and 1 <= len(v1_name.split()) <= 5:
        cands.append((v1_name, 0.8, "v1"))
    h_name, h_conf = _name_from_header(text)
    if h_name:
        cands.append((h_name, h_conf, "header"))
    e_name = _name_from_email(emails)
    if e_name:
        cands.append((e_name, 0.45, "email"))
    if not cands:
        return F()
    # boost candidates whose tokens appear in the e-mail local part
    email_user = "".join(re.sub(r"\d+", "", e.split("@")[0]).lower() for e in emails)
    scored = []
    for name, conf, src in cands:
        toks = [t.lower().strip(".") for t in name.split() if len(t) > 2]
        if email_user and any(t in email_user for t in toks):
            conf = min(0.97, conf + 0.12)
        scored.append((conf, name, src))
    conf, name, src = max(scored)
    return F(name, conf, src)


def extract_surname(full_name: str) -> dict:
    toks = full_name.split()
    if len(toks) >= 2:
        last = toks[-1].strip(".")
        if len(last) >= 3:
            return F(last.capitalize(), 0.6, "derived from full name")
    return F()


# ── emails ───────────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def extract_emails(text: str) -> tuple[list[str], dict]:
    norm = (text.replace(" @ ", "@").replace("(at)", "@").replace("[at]", "@")
                .replace("(dot)", ".").replace("[dot]", "."))
    found: list[str] = []
    for m in EMAIL_RE.finditer(norm):
        e = m.group(0).lower().strip(".")
        if len(e) <= 60 and e not in found:
            found.append(e)
    v = v1()
    for e in (_safe(v.get("email"), text[:4000], default=[]) or []):
        e = e.lower()
        if e not in found and EMAIL_RE.fullmatch(e):
            found.append(e)
    found = found[:3]
    value = [{"emailAddress": e, "isPrimary": i == 0} for i, e in enumerate(found)]
    return found, F(value, 0.95 if found else 0, "regex")


# ── phones ───────────────────────────────────────────────────────────────────

_REGION_FOR = {"India": "IN", "Nigeria": "NG", "Ghana": "GH", "Kenya": "KE", "Tanzania": "TZ",
               "Uganda": "UG", "Zambia": "ZM", "Ethiopia": "ET", "South Africa": "ZA",
               "Saudi Arabia": "SA", "United Arab Emirates": "AE", "Qatar": "QA", "Oman": "OM",
               "Kuwait": "KW", "Bahrain": "BH", "Bangladesh": "BD", "Nepal": "NP", "Sri Lanka": "LK",
               "Indonesia": "ID", "Malaysia": "MY", "Philippines": "PH", "Vietnam": "VN",
               "Thailand": "TH", "United Kingdom": "GB", "United States": "US"}


def extract_phones(text: str, country: str) -> dict:
    head = text[:5000]
    region_order = [r for r in [_REGION_FOR.get(country), "IN", "NG"] if r]
    seen: dict[str, tuple[int, str, str]] = {}  # national digits → (position, cc, national)
    try:
        import phonenumbers
        for region in dict.fromkeys(region_order):
            for m in phonenumbers.PhoneNumberMatcher(head, region, leniency=phonenumbers.Leniency.VALID):
                num = m.number
                if not phonenumbers.is_valid_number(num):
                    continue
                nat = str(num.national_number)
                if nat in seen:
                    continue
                seen[nat] = (m.start, f"+{num.country_code}", nat)
    except Exception as exc:
        log.debug("phonenumbers failed: %s", exc)
    # regex fallback (handles OCR spacing like 70345 77995)
    for m in re.finditer(r"(?<!\d)(\+?\d[\d\s\-().]{8,16}\d)(?!\d)", head):
        digits = re.sub(r"\D", "", m.group(1))
        if digits.startswith("00"):
            digits = digits[2:]
        cc, nat = "", ""
        if digits.startswith("91") and len(digits) == 12 and digits[2] in "6789":
            cc, nat = "+91", digits[2:]
        elif digits.startswith("234") and len(digits) == 13:
            cc, nat = "+234", digits[3:]
        elif len(digits) == 10 and digits[0] in "6789":
            cc, nat = C.DIAL_CODES.get(country, "+91") if country == "India" or not country else "+91", digits
            if country == "Nigeria":
                cc, nat = "+234", digits
        elif len(digits) == 11 and digits[0] == "0" and digits[1] in "789":
            cc, nat = "+234", digits[1:]
        elif len(digits) == 11 and digits[0] == "0" and digits[1] in "6789":
            cc, nat = "+91", digits[1:]
        if nat and nat not in seen and not re.fullmatch(r"(\d)\1{6,}", nat):
            seen[nat] = (m.start(), cc, nat)
    items = sorted(seen.values())[:3]
    value = [{"countryCode": cc, "mobileNumber": nat, "isPrimary": i == 0}
             for i, (_pos, cc, nat) in enumerate(items)]
    return F(value, 0.92 if value else 0, "phonenumbers")


# ── job title ────────────────────────────────────────────────────────────────

def _clean_role(s: str) -> str:
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"\b(a|an|the|as|at|in|for|of|with|and|&)\b\s*$", "", s.strip(), flags=re.I)
    s = re.sub(r"[^A-Za-z&/\- ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -/&")
    toks = s.split()
    # keep only the tail that ends at the role word, max 5 tokens
    return " ".join(toks[-5:]).title().replace("And", "and").replace("Of", "of").replace("&", "&")


def extract_job_title(text: str, years: float | None) -> dict:
    cands: list[tuple[str, float, str]] = []
    low_head = text[:2500]
    # 1. explicit labels
    for pat in (r"(?:designation|position|role|job title|current role|current position)\s*[:\-–]\s*([^\n|,]{3,60})",
                r"(?:working|worked|serving)\s+as\s+(?:an?\s+)?([^\n|,.]{3,60}?)\s+(?:in|at|with|for|since|from)\b",
                r"(?:experience|experienced)\s+(?:as|in)\s+(?:an?\s+)?([^\n|,.]{3,60}?)\s+(?:in|at|with|for|since|from|who)\b"):
        m = re.search(pat, low_head, re.I)
        if m and ROLE_PHRASE.search(m.group(1)):
            cands.append((_clean_role(ROLE_PHRASE.search(m.group(1)).group(1)), 0.9, "label"))
    # 2. header lines (title usually sits right under the name)
    for ln in _lines(text)[:6]:
        if len(ln) <= 60 and not re.search(r"@|\d{5,}", ln):
            m = ROLE_PHRASE.search(ln)
            if m and len(ln.split()) <= 8:
                cands.append((_clean_role(m.group(1)), 0.85, "header"))
                break
    # 3. summary sentence: "...experience in Electrical and Instrumental Technician..."
    for m in ROLE_PHRASE.finditer(low_head):
        phrase = _clean_role(m.group(1))
        if len(phrase.split()) >= 1 and not re.search(r"engineering|technology|degree|diploma", phrase, re.I):
            cands.append((phrase, 0.6, "summary"))
            if len(cands) >= 6:
                break
    # 4. v1 (uses the AVR job-title API + keyword map)
    v1_title = _safe(v1().get("job"), text, default=None)
    if v1_title and not (v1_title == "Fresher" and (years or 0) >= 1):
        cands.append((str(v1_title), 0.65, "v1"))
    if not cands:
        if years is not None and years < 0.5 and re.search(r"\bfresher\b", text, re.I):
            return F("Fresher", 0.8, "fresher keyword")
        return F()
    # normalise to the dropdown
    options = get_job_titles()
    best: tuple[float, str, str, bool] | None = None
    for raw, conf, src in cands:
        matched, score = match_job_title(raw, options)
        if matched:
            total = conf * 0.5 + score / 100 * 0.5 + 0.05
            cand = (total, matched, f"{src} → matched '{raw}'", True)
        else:
            cand = (conf * 0.6, raw, f"{src} (no dropdown match)", False)
        if best is None or cand[0] > best[0]:
            best = cand
    total, title, src, matched = best
    d = F(title, total, src)
    d["matchedOption"] = matched
    d["candidates"] = [c[0] for c in cands[:5]]
    return d


# ── experience ───────────────────────────────────────────────────────────────

def extract_experience(text: str) -> tuple[float | None, dict]:
    head = text[:3000]
    years: float | None = None
    conf, src = 0.0, ""
    # explicit statement: "about 10 years", "6+ years of experience", "3.5 yrs"
    m = re.search(r"(?:over|about|around|nearly|more than|having|with)?\s*(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)\b[^.\n]{0,40}?(?:experience|exp\b|in\b)",
                  head, re.I) or re.search(r"experience\D{0,25}(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)", head, re.I)
    if m:
        val = float(m.group(1))
        if 0 < val <= 45:
            years, conf, src = val, 0.85, "explicit statement"
    if years is None:
        v1_exp = _safe(v1().get("exp"), text, default="") or ""
        m2 = re.search(r"(\d{1,2})", str(v1_exp))
        if m2 and int(m2.group(1)) > 0:
            years, conf, src = float(m2.group(1)), 0.7, "v1 date ranges"
    if years is None:
        # count date ranges ourselves (YYYY – YYYY/Present)
        spans = re.findall(r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|till date|now)", text, re.I)
        total = 0
        for a, b in spans:
            end = date.today().year if not b.isdigit() else int(b)
            if 0 <= end - int(a) <= 45:
                total += end - int(a)
        if total > 0:
            years, conf, src = float(min(total, 45)), 0.55, "date ranges"
    if years is None and re.search(r"\bfresher\b", text, re.I):
        years, conf, src = 0.0, 0.8, "fresher keyword"
    if years is None:
        return None, F()
    d = F(C.experience_bucket(years), conf, src)
    d["years"] = years
    return years, d


# ── education ────────────────────────────────────────────────────────────────

def extract_education(text: str) -> dict:
    sec = _section(text, r"education(al)?( qualifications?| details| background)?|academic( qualifications?| profile| details| background)?|qualifications?")
    for scope, conf in ((sec, 0.85), (text, 0.7)):
        if not scope:
            continue
        low = scope.lower()
        for pat, option in C.EDUCATION_KEYWORDS:
            if re.search(pat, low):
                return F(option, conf, "education section" if scope is sec else "full text")
    v1_edu = _safe(v1().get("edu"), text, default="") or ""
    if v1_edu and v1_edu in C.EDUCATION_OPTIONS and v1_edu != "Intermediate / 12th":
        return F(v1_edu, 0.55, "v1")
    return F()


# ── certificates ─────────────────────────────────────────────────────────────

def extract_certificates(text: str) -> dict:
    sec = _section(text, r"certifications?|certificates?|trainings?( and certifications?)?|licenses?|professional (qualifications?|certifications?)", 20)
    scope = (sec + "\n" + text[:6000]).lower()
    found: list[str] = []
    keys = {
        "Boiler Operation Engineer (BOE)": r"\bboe\b|boiler operation engineer",
        "First Class Boiler Attendant": r"first class boiler",
        "Second Class Boiler Attendant": r"second class boiler",
        "Electrical Supervisor License": r"electrical supervisor",
        "Electrical Wireman License": r"wireman",
        "NEBOSH IGC": r"nebosh", "IOSH Managing Safely": r"\biosh\b", "OSHA 30": r"\bosha\b",
        "HSE Level 3": r"hse\s*(level\s*)?3", "HSE Level 2": r"hse\s*(level\s*)?2", "HSE Level 1": r"hse\s*(level\s*)?1",
        "First Aid / CPR": r"first aid|\bcpr\b", "Fire Safety": r"fire (safety|fighting)",
        "Work at Height": r"work(ing)? at height", "Confined Space Entry": r"confined space",
        "Rigging & Lifting": r"rigging", "Welding Certificate (6G)": r"\b6g\b|welding certif",
        "ISO 9001 Internal Auditor": r"iso\s*9001", "ISO 45001 Internal Auditor": r"iso\s*45001",
        "PLC / SCADA Training": r"\bplc\b|\bscada\b", "DCS Training": r"\bdcs\b", "AutoCAD": r"auto\s?cad",
        "Driving License": r"driving licen[cs]e", "Passport": r"passport\s*(no|number|:)",
    }
    for name, pat in keys.items():
        if re.search(pat, scope):
            found.append(name)
    value = [{"name": n, "fileId": None} for n in found[:6]]
    return F(value, 0.5 if value else 0, "keyword scan")


# ── locations ────────────────────────────────────────────────────────────────

def _find_state(scope: str, country: str) -> str:
    low = scope.lower()
    countries = [country] if country in C.STATES else list(C.STATES.keys())
    for c in countries:
        for st in sorted(C.STATES[c], key=len, reverse=True):
            if re.search(r"(?<![a-z])" + re.escape(st.lower()) + r"(?![a-z])", low):
                return st
    if country == "India":
        m = re.search(r"\b(TN|TG|AP|KA|KL|MH|DL|UP|WB|GJ|RJ|MP|PB|HR|OD|CG|JH|BR)\b\s*[-–,]?\s*\d{6}", scope)
        code = {"TN": "Tamil Nadu", "TG": "Telangana", "AP": "Andhra Pradesh", "KA": "Karnataka",
                "KL": "Kerala", "MH": "Maharashtra", "DL": "Delhi", "UP": "Uttar Pradesh",
                "WB": "West Bengal", "GJ": "Gujarat", "RJ": "Rajasthan", "MP": "Madhya Pradesh",
                "PB": "Punjab", "HR": "Haryana", "OD": "Odisha", "CG": "Chhattisgarh",
                "JH": "Jharkhand", "BR": "Bihar"}
        if m:
            return code[m.group(1)]
    return ""


def _find_city(scope: str, country: str, prefer: str = "first") -> tuple[str, str, str]:
    """Find a known city. prefer='first' for header scans, 'last' for address strings
    (addresses run specific → general, so the city sits near the end)."""
    low = scope.lower()
    best: tuple[int, str, str, str] | None = None
    for city, (st, c) in C.CITY_LOOKUP.items():
        if country and c != country:
            continue
        for m in re.finditer(r"(?<![a-z])" + re.escape(city) + r"(?![a-z])", low):
            # "Aba Road" is a street named after a city, not the city itself
            if re.match(r"\s+(road|rd|street|st|lane|avenue|ave|junction|express\w*|bypass|by-pass)\b", low[m.end():]):
                continue
            pos = m.start()
            if best is None or (pos < best[0] if prefer == "first" else pos > best[0]):
                best = (pos, city.title(), st, c)
    if best:
        return best[1], best[2], best[3]
    return "", "", ""


def extract_current_location(text: str, country: str, c_conf: float) -> dict:
    head = text[:1800]
    # 1. explicit "Location:" / "Current location:" label
    m = re.search(r"(?:current(?:ly)?\s*(?:work(?:ing)?\s*)?location|location|based in|residing at|present address)\s*[:\-–]?\s*([^\n|]{3,80})", head, re.I)
    scope = m.group(1) if m else ""
    src = "label"
    # 2. the job that is still running ("2016 – Present") — its line and the 2 lines above it
    if not scope:
        lines = _lines(text)
        for i, ln in enumerate(lines):
            if re.search(r"\b(present|current(ly)?|till date|till now|to date|ongoing)\b", ln, re.I) and re.search(r"(19|20)\d{2}", ln):
                block = " | ".join(lines[max(0, i - 2): i + 2])
                if _find_city(block, country)[0] or _find_state(block, country):
                    scope, src = block, "current job line"
                    break
    if not scope:
        scope, src = head, "header scan"
    city, st, c = _find_city(scope, country)
    state = st or _find_state(scope, country or c)
    ctry = c or country
    if not (city or state) and src == "header scan":
        # try v1 (India-only) as a last resort
        loc = _safe(v1().get("loc"), text, default=None) or {}
        city, state = loc.get("city", "") or city, loc.get("state", "") or state
        ctry = ctry or ("India" if (city or state) else "")
    value = {"country": ctry, "state": state, "city": city}
    conf = 0.0
    if city or state:
        conf = 0.8 if (city and state) else 0.6
        if src != "header scan":
            conf = min(0.95, conf + 0.1)
    elif ctry:
        conf = 0.5 * c_conf
    return F(value, conf, src)


def _address_ok(addr: str) -> bool:
    if not addr or not (10 <= len(addr) <= 220):
        return False
    low = addr.lower()
    if re.search(r"\b(updating|managing|developed|responsible|experience|skills?|engineered|implemented|ensure|using|used)\b", low):
        return False
    signals = len(re.findall(r"\d|\b(no|door|plot|flat|house|street|st|road|rd|lane|nagar|colony|village|post|p\.?o|dist|district|taluk|mandal|block|sector|phase|layout|avenue|close|crescent|estate|area|lga|l\.g\.a|near|opp|behind|pin|pincode)\b", low))
    return signals >= 1 or low.count(",") >= 2


def extract_permanent_address(text: str, country: str, c_conf: float) -> dict:
    addr = ""
    conf, src = 0.0, ""
    # labelled block
    m = re.search(r"(?:permanent|present|residential|home|postal|contact)?\s*address\s*[:\-–]\s*([^\n]{6,200}(?:\n(?![A-Za-z ]{3,30}\s*[:\-–])[^\n]{3,120}){0,2})", text, re.I)
    if m:
        cand = re.sub(r"\s+", " ", m.group(1)).strip(" ,.-")
        cand = re.sub(r"\s*(mobile|phone|email|e-mail|contact|dob|date of birth)\b.*$", "", cand, flags=re.I).strip(" ,.-")
        if _address_ok(cand):
            addr, conf, src = cand, 0.85, "address label"
    if not addr:
        v1a = _safe(v1().get("addr"), text, default={}) or {}
        cand = re.sub(r"\s+", " ", (v1a.get("address") or "")).strip(" ,.-")
        if _address_ok(cand):
            addr, conf, src = cand, 0.6, "v1"
    scope = addr if addr else text[:2500]
    prefer = "last" if addr else "first"
    if not addr:
        # "Native: Madurai, Tamilnadu" / "Home town: Erode" / "Permanent: ..." tells us the permanent place
        nm = re.search(r"(?:native(?: place)?|home\s*town|permanent(?: location| place)?)\s*[:\-–]\s*([^\n|]{3,80})", text, re.I)
        if nm:
            scope, prefer, src = nm.group(1), "first", "native/home-town label"
    city, st, c = _find_city(scope, country, prefer=prefer)
    state = st or _find_state(scope, country or c)
    pin = ""
    for pm in re.finditer(r"(?<!\d)(\d{6})(?!\d)", scope):
        p = pm.group(1)
        if p[0] != "0" and not re.search(r"\d" + p + r"|" + p + r"\d", scope):
            pin = p
            break
    ctry = c or country
    if not ctry and (state or city):
        for cc, states in C.STATES.items():
            if state in states:
                ctry = cc
                break
    value = {"address": addr, "city": city, "state": state, "country": ctry, "pinCode": pin if ctry in ("", "India") else ""}
    if not any(value.values()):
        return F()
    if addr:
        return F(value, conf, src)
    parts = sum(bool(x) for x in (city, state, pin))
    return F(value, (0.75 if src else 0.6) if parts >= 2 else 0.45 if parts == 1 else 0.4 * c_conf,
             src or "partial (city/state/pin scan)")


# ── identity numbers ─────────────────────────────────────────────────────────

def extract_pan(text: str) -> dict:
    m = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text.upper())
    if m:
        return F(m.group(1), 0.9 if m.group(1)[3] == "P" else 0.6, "regex")
    return F()


def extract_aadhaar(text: str, phones: list[str]) -> dict:
    for m in re.finditer(r"(?<!\d)([2-9]\d{3})[\s\-]?(\d{4})[\s\-]?(\d{4})(?!\d)", text):
        digits = "".join(m.groups())
        if any(digits.endswith(p) or p.endswith(digits) for p in phones):
            continue
        ctx = text[max(0, m.start() - 40):m.start()].lower()
        conf = 0.9 if re.search(r"aadha?ar|uid|uidai", ctx) else 0.55
        return F(digits, conf, "regex")
    return F()


# ── main entry ───────────────────────────────────────────────────────────────

def extract(text: str) -> tuple[dict, dict]:
    """
    Returns (fields, meta).
    fields: {fieldKey: descriptor} in the review-form shape.
    meta:   detected country, timing, which engine ran.
    """
    t0 = time.perf_counter()
    text = text or ""
    country, c_conf = detect_country(text)

    emails, f_emails = extract_emails(text)
    f_name = extract_name(text, emails)
    f_surname = extract_surname(f_name["value"])
    f_phones = extract_phones(text, country)
    phone_digits = [p["mobileNumber"] for p in f_phones["value"]] if isinstance(f_phones["value"], list) else []
    years, f_exp = extract_experience(text)
    f_job = extract_job_title(text, years)
    f_edu = extract_education(text)
    f_cert = extract_certificates(text)
    f_cur = extract_current_location(text, country, c_conf)
    f_addr = extract_permanent_address(text, country, c_conf)
    f_pan = extract_pan(text)
    f_aad = extract_aadhaar(text, phone_digits)

    # fill country defaults so the dropdowns are never blank when we know the country
    for f in (f_cur, f_addr):
        if isinstance(f["value"], dict) and not f["value"].get("country") and country:
            f["value"]["country"] = country
            if f["status"] == MISSING:
                f.update(status=LOW, confidence=round(0.4 * c_conf, 2), source="country detection")

    fields = {
        "fullName": f_name, "surname": f_surname, "emails": f_emails, "mobileNumbers": f_phones,
        "jobTitle": f_job, "yearsOfExperience": f_exp, "educationQualification": f_edu,
        "certificates": f_cert, "currentWorkLocation": f_cur, "permanentAddress": f_addr,
        "pan": f_pan, "aadhar": f_aad,
    }
    n_ok = sum(1 for f in fields.values() if f["status"] == EXTRACTED)
    n_low = sum(1 for f in fields.values() if f["status"] == LOW)
    core = [fields["fullName"], fields["emails"], fields["mobileNumbers"]]
    core_ok = sum(1 for f in core if f["status"] != MISSING)
    status = "success" if core_ok == 3 else "partial" if core_ok else "failed"
    meta = {
        "detectedCountry": country, "countryConfidence": round(c_conf, 2),
        "defaultDialCode": C.DIAL_CODES.get(country, "+91"),
        "fieldsExtracted": n_ok, "fieldsLowConfidence": n_low,
        "fieldsMissing": len(fields) - n_ok - n_low,
        "extractionStatus": status, "v1Engine": bool(v1()),
        "durationMs": int((time.perf_counter() - t0) * 1000),
        "appliedDate": date.today().isoformat(),
    }
    return fields, meta

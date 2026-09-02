"""
AVR Resume Extractor v2 — Review & Store backend
================================================
Route prefix : /resume-extractor-v2      Port : 8001   (v1 on 8000 — never touched)
Swagger      : /resume-extractor-v2/docs

Flow
  1. POST /extract            upload resume  → uid + per-field {value,status,confidence}
  2. GET  /files/{uid}        the stored resume, for the Resume Preview pane
  3. POST /certificates/{uid} optional certificate uploads
  4. POST /review             the Review & Edit column → stored in DB as training data
                              (extracted vs reviewed diff computed server-side)
Admin (x-api-key header)
  GET /records, /records/{uid}, /training/export, /stats
"""
from __future__ import annotations

import logging
import mimetypes
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse

from app_v2 import __version__
from app_v2 import constants as C
from app_v2.config import (ALLOWED_CERT_EXT, ALLOWED_EXT, ALLOWED_ORIGINS, API_KEY, API_PREFIX,
                           CERT_DIR, MAX_CERT_MB, MAX_FILE_MB, MAX_RECORDS, UPLOAD_DIR,
                           WEBHOOK_KEY, WEBHOOK_URL)
from app_v2.extractor import extract
from app_v2.job_titles import get_departments, get_job_titles, job_titles_live
from app_v2.schemas import ReviewSubmit, build_corrections
from app_v2.store import get_store
from app_v2.textract import file_to_text
from app_v2.ui import HTML as _UI_HTML

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("resume_v2")


@asynccontextmanager
async def lifespan(_: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(CERT_DIR, exist_ok=True)
    get_store()  # creates tables / indexes
    if API_KEY in ("avr_v2_change_me", "avr_dev_key", ""):
        log.warning("RESUME_V2_KEY is not set — admin endpoints use an insecure default key!")
    try:
        get_job_titles()
    except Exception as exc:  # pragma: no cover
        log.warning("job title preload failed: %s", exc)
    yield


app = FastAPI(
    title="AVR Resume Extractor v2",
    description=(
        "Upload a resume → review the extracted fields → submit the reviewed data. "
        "The reviewed record and the extracted-vs-reviewed diff are stored in the database "
        "(SQLite / AWS RDS / MongoDB) as training data.\n\n"
        "**Public**: `/extract`, `/files/{uid}`, `/certificates/{uid}`, `/review`, `/options`\n\n"
        "**Admin** (`x-api-key` header): `/records`, `/records/{uid}`, `/training/export`, `/stats`"
    ),
    version=__version__,
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _global_err(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": type(exc).__name__, "detail": str(exc)})


# ── auth ─────────────────────────────────────────────────────────────────────

def require_key(
    x_api_key: Annotated[Optional[str], Header(alias="x-api-key")] = None,
    x_api_key_q: Annotated[Optional[str], Query(alias="x_api_key", include_in_schema=False)] = None,
):
    key = x_api_key or x_api_key_q
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


Admin = Depends(require_key)


# ── helpers ──────────────────────────────────────────────────────────────────

def _ext_of(name: str | None) -> str:
    return os.path.splitext(name or "")[1].lower()


def _file_url(uid: str) -> str:
    return f"{API_PREFIX}/files/{uid}"


def _cert_url(cert_id: str) -> str:
    return f"{API_PREFIX}/certificates/file/{cert_id}"


def _public_record(rec: dict) -> dict:
    """Shape of an extraction record as the UI needs it."""
    return {
        "uid": rec["uid"],
        "filename": rec["filename"],
        "fileUrl": _file_url(rec["uid"]),
        "mime": rec.get("mime"),
        "sizeBytes": rec.get("size_bytes"),
        "status": rec.get("proc_status"),
        "extractMethod": rec.get("extract_method"),
        "durationMs": rec.get("duration_ms"),
        "error": rec.get("error_msg"),
        "reviewStatus": rec.get("review_status", "pending"),
        "createdAt": rec.get("created_at"),
        "meta": rec.get("meta", {}),
        "fields": rec.get("extracted", {}),
    }


# ── 1. Health ────────────────────────────────────────────────────────────────

@app.get(f"{API_PREFIX}/health", tags=["Health"], summary="Health check — no auth")
def health():
    store = get_store()
    return {
        "status": "running", "version": __version__, "port": 8001, "v1_port": 8000,
        "database": store.backend, "dbOk": store.ping(),
        "jobTitlesLive": job_titles_live(),
        "acceptedFormats": sorted(ALLOWED_EXT), "maxFileMb": MAX_FILE_MB,
        "recordsKept": "all" if MAX_RECORDS == 0 else MAX_RECORDS,
        "uploadDir": UPLOAD_DIR,
    }


# ── 2. Options for the dropdowns ─────────────────────────────────────────────

@app.get(f"{API_PREFIX}/options", tags=["Options"], summary="Dropdown lists for the review form")
def options(refresh: bool = Query(False, description="Force re-fetch of job titles from the AVR API")):
    titles = get_job_titles(force=refresh)
    return {
        "jobTitles": titles,
        "departments": get_departments(),
        "jobTitlesSource": "avr-api" if job_titles_live() else "fallback",
        "experience": C.EXPERIENCE_BUCKETS,
        "education": C.EDUCATION_OPTIONS,
        "certificates": C.CERTIFICATE_OPTIONS,
        "countries": C.COUNTRIES,
        "states": C.STATES,
        "countryCodes": C.COUNTRY_CODE_OPTIONS,
        "dialCodes": C.DIAL_CODES,
    }


# ── 3. Extract ───────────────────────────────────────────────────────────────

@app.post(f"{API_PREFIX}/extract", tags=["Extract"], summary="Upload resume → extracted fields with status per field")
async def extract_resume(
    file: Annotated[UploadFile, File(description="Resume: PDF, DOC, DOCX, RTF, TXT or image")],
):
    """
    Returns `uid` (use it for `/files/{uid}`, `/certificates/{uid}` and `/review`) plus
    `fields`, one entry per review-form field:

    | key | value shape |
    |---|---|
    | fullName, surname, jobTitle, yearsOfExperience, educationQualification, pan, aadhar | string |
    | emails | `[{emailAddress, isPrimary}]` |
    | mobileNumbers | `[{countryCode, mobileNumber, isPrimary}]` |
    | certificates | `[{name, fileId}]` |
    | currentWorkLocation | `{country, state, city}` |
    | permanentAddress | `{address, city, state, country, pinCode}` |

    Every field carries `status` = `extracted` (green) / `low_confidence` (amber) /
    `not_extracted` (red), `confidence` 0–1 and `source`.
    """
    ext = _ext_of(file.filename)
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported format '{ext or 'none'}'. Allowed: {', '.join(sorted(ALLOWED_EXT))}")
    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file uploaded")
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_MB} MB limit")

    uid = uuid.uuid4().hex
    stored_path = os.path.join(UPLOAD_DIR, f"{uid}{ext}")
    with open(stored_path, "wb") as fh:
        fh.write(content)

    t0 = time.perf_counter()
    text, method = file_to_text(stored_path, file.filename)
    error = None
    if not text or len(text.strip()) < 20:
        fields, meta = extract("")
        status = "failed"
        error = ("Could not extract text from file. If this is a scanned document, "
                 "make sure OCR is installed on the server.")
    else:
        fields, meta = extract(text)
        status = meta["extractionStatus"]
    ms = int((time.perf_counter() - t0) * 1000)
    meta.update(extractMethod=method, textLength=len(text or ""), durationMs=ms)

    rec = dict(
        uid=uid, filename=file.filename or f"{uid}{ext}", stored_path=stored_path,
        mime=file.content_type or mimetypes.guess_type(stored_path)[0], size_bytes=len(content),
        extract_method=method, proc_status=status, duration_ms=ms, error_msg=error,
        raw_text=text, extracted=fields, meta=meta,
    )
    get_store().save_extraction(rec)
    log.info("extracted uid=%s file=%s status=%s method=%s ms=%s", uid, file.filename, status, method, ms)

    out = _public_record({**rec, "review_status": "pending", "created_at": None})
    out["textPreview"] = (text or "")[:600]
    return out


# ── 4. Serve the stored resume for the preview pane ──────────────────────────

@app.get(f"{API_PREFIX}/files/{{uid}}", tags=["Extract"], summary="Download / preview the uploaded resume")
def get_file(uid: str, download: bool = Query(False)):
    rec = get_store().get_extraction(uid)
    if not rec or not rec.get("stored_path") or not os.path.exists(rec["stored_path"]):
        raise HTTPException(404, "File not found")
    media = rec.get("mime") or mimetypes.guess_type(rec["stored_path"])[0] or "application/octet-stream"
    disposition = "attachment" if download else "inline"
    return FileResponse(rec["stored_path"], media_type=media,
                        headers={"Content-Disposition": f'{disposition}; filename="{rec["filename"]}"'})


# ── 5. Certificates ──────────────────────────────────────────────────────────

@app.post(f"{API_PREFIX}/certificates/{{uid}}", tags=["Certificates"], summary="Upload one certificate file for a candidate")
async def upload_certificate(
    uid: str,
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form(max_length=200)] = "",
):
    store = get_store()
    if not store.get_extraction(uid):
        raise HTTPException(404, f"Unknown uid '{uid}' — extract a resume first")
    ext = _ext_of(file.filename)
    if ext not in ALLOWED_CERT_EXT:
        raise HTTPException(400, f"Unsupported certificate format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_CERT_EXT))}")
    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")
    if len(content) > MAX_CERT_MB * 1024 * 1024:
        raise HTTPException(413, f"Certificate exceeds {MAX_CERT_MB} MB limit")
    cert_id = uuid.uuid4().hex
    path = os.path.join(CERT_DIR, f"{cert_id}{ext}")
    with open(path, "wb") as fh:
        fh.write(content)
    store.save_certificate(dict(cert_id=cert_id, uid=uid, name=name.strip(), filename=file.filename,
                                stored_path=path, size_bytes=len(content)))
    return {"fileId": cert_id, "uid": uid, "name": name.strip(), "fileName": file.filename,
            "fileUrl": _cert_url(cert_id), "sizeBytes": len(content)}


@app.get(f"{API_PREFIX}/certificates/file/{{cert_id}}", tags=["Certificates"], summary="Download a certificate file")
def get_certificate(cert_id: str):
    cert = get_store().get_certificate(cert_id)
    if not cert or not os.path.exists(cert.get("stored_path", "")):
        raise HTTPException(404, "Certificate not found")
    media = mimetypes.guess_type(cert["stored_path"])[0] or "application/octet-stream"
    return FileResponse(cert["stored_path"], media_type=media,
                        headers={"Content-Disposition": f'inline; filename="{cert.get("filename")}"'})


# ── 6. Review → store (the "Submit for Data Training" button) ────────────────

def _forward_webhook(payload: dict) -> str:
    if not WEBHOOK_URL:
        return "disabled"
    try:
        import requests
        headers = {"Content-Type": "application/json"}
        if WEBHOOK_KEY:
            headers["x-api-key"] = WEBHOOK_KEY
        r = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=15)
        return f"{r.status_code}"
    except Exception as exc:
        log.warning("webhook failed: %s", exc)
        return f"error: {exc}"[:60]


@app.post(f"{API_PREFIX}/review", tags=["Review"], summary="Submit the reviewed/edited fields → stored in DB")
def submit_review(body: ReviewSubmit):
    """
    Send exactly what is in the **Review & Edit** column. The server:

    1. loads the AI-extracted values for `uid`
    2. diffs them against the reviewed values (`confirmed` / `corrected` / `filled` / `cleared`)
    3. stores the reviewed record + diff in the database (training data)
    4. optionally forwards the reviewed record to `REVIEW_WEBHOOK_URL`
    """
    store = get_store()
    rec = store.get_extraction(body.uid)
    if not rec:
        raise HTTPException(404, f"Unknown uid '{body.uid}' — extract a resume first")

    reviewed = body.fields.model_dump()
    corrections, total, changed = build_corrections(rec.get("extracted", {}), reviewed)
    accuracy = int(round(100 * (total - changed) / total)) if total else 0

    # attach certificate file names for stored certificates
    certs = {c["cert_id"]: c for c in store.list_certificates(body.uid)}
    for c in reviewed.get("certificates", []):
        if c.get("fileId") and c["fileId"] in certs:
            c["fileName"] = certs[c["fileId"]].get("filename")
            c["fileUrl"] = _cert_url(c["fileId"])

    candidate_record = {
        "uid": body.uid,
        "resume": _file_url(body.uid),
        "resumeFileName": rec["filename"],
        "isEmployee": "candidate",
        "appliedDate": rec.get("meta", {}).get("appliedDate"),
        "reviewer": body.reviewer,
        **reviewed,
    }
    webhook_status = _forward_webhook(candidate_record)

    review_id = store.save_review(dict(
        uid=body.uid, reviewer=body.reviewer, reviewed=reviewed, corrections=corrections,
        fields_total=total, fields_changed=changed, accuracy_pct=accuracy,
        notes=body.notes, webhook_status=webhook_status,
    ))
    log.info("review saved uid=%s id=%s changed=%s/%s accuracy=%s%%", body.uid, review_id, changed, total, accuracy)
    return {
        "ok": True, "reviewId": review_id, "uid": body.uid,
        "storedIn": store.backend, "webhook": webhook_status,
        "fieldsTotal": total, "fieldsChanged": changed, "extractionAccuracyPct": accuracy,
        "changedFields": [k for k, v in corrections.items() if v["changed"]],
        "candidate": candidate_record,
    }


# ── 7. Admin ─────────────────────────────────────────────────────────────────

@app.get(f"{API_PREFIX}/records", tags=["Admin"], summary="List extractions (newest first) — requires API key")
def list_records(_: bool = Admin, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    rows, total = get_store().list_extractions(limit=limit, offset=offset)
    return {"total": total, "limit": limit, "offset": offset,
            "records": [_public_record(r) for r in rows]}


@app.get(f"{API_PREFIX}/records/{{uid}}", tags=["Admin"], summary="One extraction with all its reviews — requires API key")
def get_record(uid: str, _: bool = Admin):
    store = get_store()
    rec = store.get_extraction(uid)
    if not rec:
        raise HTTPException(404, f"Record '{uid}' not found")
    out = _public_record(rec)
    out["rawText"] = rec.get("raw_text")
    out["reviews"] = store.get_reviews(uid)
    out["certificates"] = [{"fileId": c["cert_id"], "name": c.get("name"), "fileName": c.get("filename"),
                            "fileUrl": _cert_url(c["cert_id"])} for c in store.list_certificates(uid)]
    return out


@app.get(f"{API_PREFIX}/training/export", tags=["Admin"], summary="Export all reviewed records as JSONL — requires API key")
def export_training(_: bool = Admin, limit: int = Query(10000, ge=1, le=100000)):
    import json

    def gen():
        for r in get_store().iter_training(limit=limit):
            yield json.dumps({
                "uid": r["uid"], "filename": r.get("filename"), "submitted_at": r.get("submitted_at"),
                "reviewer": r.get("reviewer"), "accuracy_pct": r.get("accuracy_pct"),
                "raw_text": r.get("raw_text"), "extracted": r.get("extracted"),
                "reviewed": r.get("reviewed"), "corrections": r.get("corrections"),
            }, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson",
                             headers={"Content-Disposition": 'attachment; filename="resume_training.jsonl"'})


@app.get(f"{API_PREFIX}/stats", tags=["Admin"], summary="Counts + average extraction accuracy — requires API key")
def stats(_: bool = Admin):
    return get_store().stats()


# ── 8. Reference UI ──────────────────────────────────────────────────────────

@app.get(f"{API_PREFIX}", response_class=HTMLResponse, include_in_schema=False)
@app.get(f"{API_PREFIX}/", response_class=HTMLResponse, include_in_schema=False)
def frontend():
    return _UI_HTML.replace("__API_PREFIX__", API_PREFIX)

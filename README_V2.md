# Resume Extractor v2 — Review & Store

Sits in the same repo as v1. **v1 (`app/`, port 8000, `/resume-extractor`) is untouched.**

v2 = the backend for the **Add Candidate V2** screen:

```
upload resume ──► POST /extract ──► Extracted Information | Review & Edit | Resume Preview
                                              │
                        reviewer edits / confirms every field
                                              │
             "Submit for Data Training" ──► POST /review ──► DATABASE (SQLite / AWS RDS / MongoDB)
                                                             stores: extracted + reviewed + per-field diff
```

## What v2 does

| | |
|---|---|
| Extraction | v1 extractors (same code as live v1) **plus** v2's own: country-aware phones (+91 / +234 …), job title → dropdown match, experience bucket, education dropdown match, Nigeria + India city/state lookup, certificates, PAN/Aadhaar |
| Per-field status | every field returns `extracted` (green ✓) / `low_confidence` (amber !) / `not_extracted` (red ✕) with `confidence` and `source` |
| Review store | reviewed values + diff (`confirmed` / `corrected` / `filled` / `cleared`) + accuracy % saved per submission |
| Database | `DATABASE_URL` → SQLite (default), **AWS RDS Postgres/MySQL**; or `MONGO_URI` → Atlas / DocumentDB |
| Files | resume stored on VPS, served back for the preview pane (`/files/{uid}`); certificate uploads |
| Options | `GET /options` gives every dropdown (job titles from the live AVR API, cached; experience; education; certificates; countries; states; dial codes) |
| Training export | `GET /training/export` → JSONL of raw text + extracted + reviewed + corrections |
| UI | reference dark UI embedded at `/resume-extractor-v2/` (same layout as the Add Candidate V2 screen) |

## URLs

| URL | What |
|---|---|
| `avrenergies.com/resume-extractor` | v1 — unchanged |
| `avrenergies.com/resume-extractor-v2/` | v2 review UI |
| `avrenergies.com/resume-extractor-v2/docs` | Swagger |
| `avrenergies.com/resume-extractor-v2/health` | health + DB check |

## Run locally

```bash
pip install -r requirements_v2.txt
python -m spacy download en_core_web_sm
set RESUME_V2_KEY=avr_dev_123        # Windows;  Linux/Mac: export RESUME_V2_KEY=avr_dev_123
python run_v2.py
# UI:      http://localhost:8001/resume-extractor-v2/
# Swagger: http://localhost:8001/resume-extractor-v2/docs
```

Data goes to `./v2_data/` (records.db + uploads) when run locally.

## Tests

```bash
pytest tests_v2 -q
```

14 tests: health, options, PDF / TXT / DOCX extraction (Indian + Nigerian resumes), bad input, file preview,
certificate upload, review round-trip + validation, admin auth, training export, UI/docs, retention purge.

## Deploy on VPS

```bash
git pull
bash deploy_v2.sh                       # copies app/ + app_v2/, venv, spaCy model, systemd
nano /opt/resume_v2/.env                # set RESUME_V2_KEY + DATABASE_URL (first time)
systemctl restart resume_v2
# first time only: add nginx_v2_location.conf into the server{} block, nginx -t, systemctl reload nginx
```

Switch to AWS RDS later by changing one line in `/opt/resume_v2/.env`:

```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST.rds.amazonaws.com:5432/DBNAME
```

Tables are created automatically (`resume_extractions`, `resume_reviews`, `resume_certificates`).

---

# API contract (for the frontend)

All paths are under `/resume-extractor-v2`. Field names are camelCase, same convention as v1.

### `GET /options`
Dropdown lists. Call once on page load.
```json
{ "jobTitles": ["Boiler Operator", "..."], "departments": [], "jobTitlesSource": "avr-api",
  "experience": ["Fresher","0-1 years","1-3 years","3-5 years","5-10 years","10+ years"],
  "education": ["10th / SSC", "...", "HND", "B.E", "B.Tech"],
  "certificates": [], "countries": ["India","Nigeria"],
  "states": {"India": [], "Nigeria": []}, "countryCodes": ["+1","+27","+91","+234"],
  "dialCodes": {"India":"+91","Nigeria":"+234"} }
```

### `POST /extract` — multipart `file`
```json
{
  "uid": "43a260ba880141b9b44af7b956b5d923",
  "filename": "resume.pdf", "fileUrl": "/resume-extractor-v2/files/43a260ba880141b9b44af7b956b5d923",
  "status": "success | partial | failed", "extractMethod": "pdf | pdf-ocr | docx | doc | txt | image",
  "durationMs": 812, "error": null,
  "meta": { "detectedCountry": "Nigeria", "defaultDialCode": "+234",
            "fieldsExtracted": 8, "fieldsLowConfidence": 2, "fieldsMissing": 2 },
  "fields": {
    "fullName":     {"value": "Calistus Iwuji", "status": "extracted", "confidence": 0.97, "source": "header"},
    "surname":      {"value": "Iwuji", "status": "low_confidence", "confidence": 0.6, "source": "derived from full name"},
    "emails":       {"value": [{"emailAddress": "x@gmail.com", "isPrimary": true}], "status": "extracted", "confidence": 0.95, "source": "regex"},
    "mobileNumbers":{"value": [{"countryCode": "+234", "mobileNumber": "7034577995", "isPrimary": true}], "status": "extracted", "confidence": 0.92, "source": "phonenumbers"},
    "jobTitle":     {"value": "Electrical Technician", "status": "extracted", "confidence": 0.85, "source": "summary", "matchedOption": true, "candidates": []},
    "yearsOfExperience":      {"value": "5-10 years", "years": 10, "status": "extracted", "confidence": 0.85, "source": "explicit statement"},
    "educationQualification": {"value": "HND", "status": "extracted", "confidence": 0.85, "source": "education section"},
    "certificates": {"value": [{"name": "HSE Level 3", "fileId": null}], "status": "low_confidence", "confidence": 0.5, "source": "keyword scan"},
    "currentWorkLocation": {"value": {"country": "Nigeria", "state": "Rivers", "city": "Port Harcourt"}, "status": "extracted", "confidence": 0.9, "source": "current job line"},
    "permanentAddress":    {"value": {"address": "No 12 Aba Road, Umuahia", "city": "Umuahia", "state": "Abia", "country": "Nigeria", "pinCode": ""}, "status": "extracted", "confidence": 0.85, "source": "address label"},
    "pan":    {"value": "", "status": "not_extracted", "confidence": 0, "source": "none"},
    "aadhar": {"value": "", "status": "not_extracted", "confidence": 0, "source": "none"}
  }
}
```
`status` → colour: `extracted` green ✓ · `low_confidence` amber ! · `not_extracted` red ✕ ("Not extracted").

### `GET /files/{uid}` — the uploaded resume (inline; `?download=1` for attachment). Use as iframe/img src for the preview pane.

### `POST /certificates/{uid}` — multipart `file` + form `name` → `{"fileId": "...", "fileUrl": "...", "name": "...", "fileName": "..."}`

### `POST /review` — JSON, the Review & Edit column exactly as shown
```json
{
  "uid": "43a260ba880141b9b44af7b956b5d923",
  "reviewer": "sharfudeen",
  "fields": {
    "fullName": "Calistus Iwuji", "surname": "Iwuji",
    "emails": [{"emailAddress": "x@gmail.com", "isPrimary": true}],
    "mobileNumbers": [{"countryCode": "+234", "mobileNumber": "7034577995", "isPrimary": true}],
    "jobTitle": "Instrumentation Technician", "yearsOfExperience": "10+ years",
    "educationQualification": "HND",
    "certificates": [{"name": "HSE Level 3", "fileId": null}],
    "currentWorkLocation": {"country": "Nigeria", "state": "Rivers", "city": "Port Harcourt"},
    "permanentAddress": {"address": "No 12 Aba Road", "city": "Umuahia", "state": "Abia", "country": "Nigeria", "pinCode": ""},
    "pan": "", "aadhar": ""
  }
}
```
Required: `fullName`, at least one valid `emails[]`, `jobTitle`. `reviewer` is optional. Response:
```json
{ "ok": true, "reviewId": 17, "uid": "...", "storedIn": "sql", "webhook": "disabled",
  "fieldsTotal": 12, "fieldsChanged": 2, "extractionAccuracyPct": 83,
  "changedFields": ["jobTitle", "yearsOfExperience"],
  "candidate": { "uid": "...", "resume": "/resume-extractor-v2/files/...", "isEmployee": "candidate", "appliedDate": "2026-09-02", "fullName": "..." } }
```
Validation errors come back as `422` with `detail[]` (`loc` + `msg`).

### Admin — header `x-api-key: <RESUME_V2_KEY>`
| Endpoint | Returns |
|---|---|
| `GET /records?limit=50&offset=0` | newest extractions with `reviewStatus` |
| `GET /records/{uid}` | one extraction + `rawText` + all `reviews[]` (reviewed + corrections) + `certificates[]` |
| `GET /training/export` | JSONL download of every reviewed record |
| `GET /stats` | `{extractions, reviews, avgAccuracyPct}` |

## Environment variables
See `.env.v2.example` — `RESUME_V2_KEY`, `DATABASE_URL` / `MONGO_URI`, `REVIEW_WEBHOOK_URL`, `MAX_RECORDS`, `ALLOWED_ORIGINS`, `OCR_ENABLED`.

## Database schema (SQL)

- `resume_extractions(uid, filename, stored_path, mime, size_bytes, extract_method, proc_status, duration_ms, error_msg, raw_text, extracted_json, meta_json, review_status, created_at)`
- `resume_reviews(uid, reviewer, reviewed_json, corrections_json, fields_total, fields_changed, accuracy_pct, notes, webhook_status, submitted_at)`
- `resume_certificates(cert_id, uid, name, filename, stored_path, size_bytes, created_at)`

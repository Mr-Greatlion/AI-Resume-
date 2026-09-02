"""
v2 configuration — everything comes from environment variables.
v1 (app/) is completely untouched.

DATABASE_URL examples
  sqlite (default)  sqlite:////opt/resume_v2/records.db
  AWS RDS Postgres  postgresql+psycopg2://user:pass@host.rds.amazonaws.com:5432/avr
  AWS RDS MySQL     mysql+pymysql://user:pass@host.rds.amazonaws.com:3306/avr
MONGO_URI (optional, takes priority over DATABASE_URL when set)
  mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
  mongodb://user:pass@docdb.cluster.amazonaws.com:27017/?tls=true
"""
from __future__ import annotations
import os

API_PREFIX      = os.getenv("V2_API_PREFIX", "/resume-extractor-v2").rstrip("/") or ""
API_KEY         = os.getenv("RESUME_V2_KEY", "avr_v2_change_me").strip()
MAX_FILE_MB     = int(os.getenv("MAX_FILE_MB", "10"))
MAX_CERT_MB     = int(os.getenv("MAX_CERT_MB", "5"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "20000"))

# 0 = keep everything (training data). >0 = keep only the newest N extractions.
MAX_RECORDS     = int(os.getenv("MAX_RECORDS", "0"))

BASE_DIR        = os.getenv("V2_BASE_DIR", "/opt/resume_v2")
UPLOAD_DIR      = os.getenv("V2_UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
CERT_DIR        = os.getenv("V2_CERT_DIR",   os.path.join(BASE_DIR, "certificates"))

DATABASE_URL    = os.getenv("DATABASE_URL", "").strip() or \
                  "sqlite:///" + os.getenv("V2_DB_PATH", os.path.join(BASE_DIR, "records.db"))
MONGO_URI       = os.getenv("MONGO_URI", "").strip()
MONGO_DB        = os.getenv("MONGO_DB", "avr_resume_v2").strip()

# Optional: POST every reviewed record to the main AVR backend as JSON.
WEBHOOK_URL     = os.getenv("REVIEW_WEBHOOK_URL", "").strip()
WEBHOOK_KEY     = os.getenv("REVIEW_WEBHOOK_KEY", "").strip()

# Job titles come from the live AVR API (cached), with a built-in fallback list.
JOB_TITLE_API   = os.getenv("JOB_TITLE_API",
                            "https://api.avrenergies.com/job-posting/departments/with-job-titles")
JOB_TITLE_TTL   = int(os.getenv("JOB_TITLE_TTL", "3600"))

# Where the v1 extractor package lives (folder that CONTAINS the `app/` package).
# Defaults to this repo root, so v2 uses the exact same extractors as v1.
V1_APP_PATH     = os.getenv("V1_APP_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()] or [
    "https://avrenergies.com", "https://www.avrenergies.com",
    "http://localhost", "http://localhost:3000", "http://localhost:5173", "http://localhost:8001",
]

ALLOWED_EXT      = {".pdf", ".doc", ".docx", ".rtf", ".txt", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
ALLOWED_CERT_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"}

OCR_ENABLED     = os.getenv("OCR_ENABLED", "1") not in ("0", "false", "False")
OCR_GPU         = os.getenv("OCR_GPU", "0") in ("1", "true", "True")

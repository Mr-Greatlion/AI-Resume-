"""
v2 config — all from environment variables.
v1 (app/) is completely untouched.
"""
import os

API_KEY       = os.getenv("RESUME_V2_KEY", "avr_v2_change_me").strip()
MAX_FILE_MB   = int(os.getenv("MAX_FILE_MB", "10"))
MAX_RECORDS   = int(os.getenv("MAX_RECORDS", "5"))
UPLOAD_DIR    = os.getenv("V2_UPLOAD_DIR", "/opt/resume_v2/uploads")
DB_PATH       = os.getenv("V2_DB_PATH",    "/opt/resume_v2/records.db")
V1_APP_PATH   = os.getenv("V1_APP_PATH",   "/opt/resume_api")   # path to existing v1

ALLOWED_EXT   = {".pdf", ".docx", ".jpg", ".jpeg", ".png", ".txt"}
API_PREFIX    = "/resume-extractor-v2"

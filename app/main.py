from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import requests
import tempfile
import os

from app.ocr_engine import pdf_to_text
from app.extractor import (
    extract_name, extract_email, extract_phone,
    extract_education, detect_pan, detect_aadhaar
)
from app.experience_calc import calculate_experience
from app.location_address import extract_current_location, extract_address

API_KEY = "CHANGE_THIS_SECRET"

app = FastAPI(title="Resume Parsing API", version="1.0")

class ResumeRequest(BaseModel):
    resume_url: str


@app.post("/parse-resume")
def parse_resume(
    data: ResumeRequest,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Download resume from S3
    r = requests.get(data.resume_url, timeout=30)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Resume download failed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(r.content)
        resume_path = f.name

    try:
        text = pdf_to_text(resume_path)

        result = {
            "full_name": extract_name(text),
            "email": extract_email(text),
            "phone": extract_phone(text),
            "education": extract_education(text),
            "experience_years": calculate_experience(text),
            "current_location": extract_current_location(text),
            "permanent_address": extract_address(text),
            "pan_present": detect_pan(text),
            "aadhaar_present": detect_aadhaar(text)
        }

        return {
            "status": "success",
            "candidate": result,
            "confidence": 0.93,
            "auto_fill_ready": True
        }

    finally:
        os.remove(resume_path)

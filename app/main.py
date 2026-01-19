from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import requests
import tempfile
import os
from datetime import date

from app.ocr_engine import pdf_to_text
from app.extractor import (
    extract_name,
    extract_email,
    extract_phone,
    extract_education,
    detect_pan,
    detect_aadhaar
)
from app.experience_calc import calculate_experience
from app.location_address import extract_current_location, extract_address

API_KEY = "CHANGE_THIS_SECRET"

app = FastAPI(
    title="AI Resume Parsing API",
    version="1.0"
)


# -------- Request Model --------
class ResumeRequest(BaseModel):
    resume: str   # S3 URL


# -------- API Endpoint --------
@app.post("/parse-resume")
def parse_resume(
    data: ResumeRequest,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Download resume
    response = requests.get(data.resume, timeout=30)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Resume download failed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(response.content)
        resume_path = tmp.name

    try:
        text = pdf_to_text(resume_path)

        # Core extraction
        name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        education = extract_education(text)
        experience = calculate_experience(text)
        location = extract_current_location(text)
        address_info = extract_address(text)

        pan_present = detect_pan(text)
        aadhaar_present = detect_aadhaar(text)

        # -------- FINAL RESPONSE (CLIENT FORMAT) --------
        result = {
            "candidateName": name,
            "jobTitle": "",
            "department": "",
            "resume": data.resume,
            "isEmployee": "candidate",
            "certificates": [],

            "address": address_info.get("address") if address_info else "",
            "state": address_info.get("state") if address_info else "",
            "country": address_info.get("country") if address_info else "india",
            "pinCode": address_info.get("pincode") if address_info else "",

            "yearsOfExperience": experience,
            "educationQualification": education,
            "currentWorkLocation": (
                f"{location['state']}, {location['country']}"
                if location else ""
            ),

            "emails": [
                {
                    "emailAddress": email,
                    "isPrimary": True
                }
            ] if email else [],

            "mobileNumbers": [
                {
                    "mobileNumber": phone,
                    "isPrimary": True
                }
            ] if phone else [],

            "pan": {
                "_id": "",
                "panNumber": "xxxxxxxxx" if pan_present else ""
            },

            "aadhar": {
                "_id": "",
                "aadharNumber": "" if not aadhaar_present else "************"
            },

            "appliedDate": date.today().isoformat()
        }

        return result

    finally:
        os.remove(resume_path)
